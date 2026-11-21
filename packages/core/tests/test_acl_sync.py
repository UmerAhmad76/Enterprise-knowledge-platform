"""ACL sync tests: content badle bina permission badle to asar ho, version na badle, aur index ke liye document list mein aaye."""
import pytest
from sqlalchemy import func, select

from core.db.models import Document, DocumentACL, DocumentVersion, Group, Source, Tenant
from core.ingestion.service import run_source_sync


@pytest.fixture
def world(db_session, tmp_path):
    tenant = Tenant(slug="acme", name="Acme")
    db_session.add(tenant)
    db_session.flush()
    eng = Group(tenant_id=tenant.id, name="eng")
    hr = Group(tenant_id=tenant.id, name="hr")
    db_session.add_all([eng, hr])
    db_session.flush()
    source = Source(
        tenant_id=tenant.id,
        kind="local_fs",
        name="docs",
        config={"root": str(tmp_path), "allowed_group_ids": [str(eng.id)]},
    )
    db_session.add(source)
    db_session.flush()
    (tmp_path / "a.md").write_text("# Doc\n\nBody text.", encoding="utf-8")
    db_session.commit()
    return {"tenant": tenant, "eng": eng, "hr": hr, "source": source, "root": tmp_path}


def sync(db_session, world):
    return run_source_sync(db_session, world["tenant"].id, world["source"].id)


def change_acl_to_hr(db_session, world):
    # Sirf permission badli, file ka content wahi hai
    world["source"].config = {
        "root": str(world["root"]),
        "allowed_group_ids": [str(world["hr"].id)],
    }
    db_session.commit()


def group_acl(db_session):
    return db_session.execute(
        select(DocumentACL.principal_id).where(DocumentACL.principal_type == "group")
    ).scalars().all()


def test_acl_change_without_content_change_is_applied(db_session, world):
    sync(db_session, world)
    change_acl_to_hr(db_session, world)

    report = sync(db_session, world)

    assert group_acl(db_session) == [world["hr"].id]
    assert report.acl_updated == 1
    assert report.unchanged == 0


def test_acl_change_keeps_version_and_marks_document_for_reindex(db_session, world):
    sync(db_session, world)
    change_acl_to_hr(db_session, world)

    report = sync(db_session, world)

    doc = db_session.execute(select(Document)).scalar_one()
    versions = db_session.execute(select(func.count()).select_from(DocumentVersion)).scalar_one()
    assert doc.current_version == 1
    assert versions == 1
    assert "a.md" in report.upserted_ids


def test_no_acl_change_is_not_counted_or_reindexed(db_session, world):
    sync(db_session, world)

    report = sync(db_session, world)

    assert report.acl_updated == 0
    assert report.unchanged == 1
    assert report.upserted_ids == []