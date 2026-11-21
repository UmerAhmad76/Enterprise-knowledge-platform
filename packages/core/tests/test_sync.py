"""End-to-end incremental sync SQLite par: new, unchanged, changed, deleted, bad file, aur tenant isolation."""
import pytest
from sqlalchemy import func, select

from core.common.errors import NotFoundError
from core.db.models import Chunk, Document, DocumentACL, DocumentVersion, Group, Source, Tenant
from core.ingestion.service import run_source_sync


@pytest.fixture
def world(db_session, tmp_path):
    tenant = Tenant(slug="acme", name="Acme")
    db_session.add(tenant)
    db_session.flush()
    group = Group(tenant_id=tenant.id, name="eng")
    db_session.add(group)
    db_session.flush()
    source = Source(
        tenant_id=tenant.id,
        kind="local_fs",
        name="docs",
        config={"root": str(tmp_path), "allowed_group_ids": [str(group.id)]},
    )
    db_session.add(source)
    db_session.flush()
    (tmp_path / "a.md").write_text("# Alpha\n\nFirst paragraph about alpha.", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Beta\n\nBeta content here.", encoding="utf-8")
    db_session.commit()
    return {"tenant": tenant, "group": group, "source": source, "root": tmp_path}


def sync(db_session, world):
    return run_source_sync(db_session, world["tenant"].id, world["source"].id)


def test_first_sync_creates_documents_chunks_and_acl(db_session, world):
    report = sync(db_session, world)
    assert report.new == 2 and report.changed == 0 and report.failed == []

    docs = db_session.execute(select(Document)).scalars().all()
    assert {d.title for d in docs} == {"Alpha", "Beta"}
    assert all(d.current_version == 1 for d in docs)

    chunk_count = db_session.execute(select(func.count()).select_from(Chunk)).scalar_one()
    assert chunk_count == 2

    acl = db_session.execute(select(DocumentACL)).scalars().all()
    assert len(acl) == 2
    assert all(a.principal_type == "group" and a.principal_id == world["group"].id for a in acl)


def test_second_sync_skips_unchanged_documents(db_session, world):
    sync(db_session, world)
    report = sync(db_session, world)
    assert report.unchanged == 2 and report.new == 0 and report.changed == 0

    versions = db_session.execute(select(func.count()).select_from(DocumentVersion)).scalar_one()
    assert versions == 2


def test_edited_file_bumps_version_and_replaces_chunks(db_session, world):
    sync(db_session, world)
    (world["root"] / "a.md").write_text("# Alpha\n\nCompletely rewritten body.", encoding="utf-8")

    report = sync(db_session, world)
    assert report.changed == 1 and report.unchanged == 1

    doc = db_session.execute(select(Document).where(Document.external_id == "a.md")).scalar_one()
    assert doc.current_version == 2

    texts = db_session.execute(
        select(Chunk.content)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.external_id == "a.md")
    ).scalars().all()
    assert any("Completely rewritten body" in t for t in texts)
    assert not any("First paragraph" in t for t in texts)


def test_deleted_file_is_retired(db_session, world):
    sync(db_session, world)
    (world["root"] / "b.md").unlink()

    report = sync(db_session, world)
    assert report.deleted == 1

    doc = db_session.execute(select(Document).where(Document.external_id == "b.md")).scalar_one()
    assert doc.status == "deleted"
    remaining = db_session.execute(
        select(func.count()).select_from(Chunk).where(Chunk.document_id == doc.id)
    ).scalar_one()
    assert remaining == 0


def test_bad_file_is_reported_without_stopping_sync(db_session, world):
    (world["root"] / "bad.md").write_bytes(b"\xff\xfe broken")

    report = sync(db_session, world)
    assert report.failed == ["bad.md"]
    assert report.new == 2


def test_other_tenants_source_is_not_found(db_session, world):
    other = Tenant(slug="globex", name="Globex")
    db_session.add(other)
    db_session.commit()
    with pytest.raises(NotFoundError):
        run_source_sync(db_session, other.id, world["source"].id)