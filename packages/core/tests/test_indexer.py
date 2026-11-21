"""Indexer tests: fake OpenSearch client ke saath. Har chunk mein ACL, tenant aur vector hona lazmi hai."""
import uuid

import pytest
from sqlalchemy import select

from core.db.models import Document, Group, Source, Tenant, User
from core.embeddings.fake import FakeEmbedder
from core.ingestion.service import run_source_sync
from core.search_index.indexer import apply_sync_report, index_document

INDEX = "chunks-test"


class FakeOpenSearch:
    """Asli OpenSearch ke bajaye calls record karta hai, taake hum dekh sakein kya bheja gaya."""

    def __init__(self) -> None:
        self.indexed: list[tuple[str, str, dict]] = []
        self.deleted: list[tuple[str, dict]] = []

    def index(self, index, id, body, refresh=False):
        self.indexed.append((index, id, body))

    def delete_by_query(self, index, body, refresh=True, conflicts="proceed"):
        self.deleted.append((index, body))


@pytest.fixture
def world(db_session, tmp_path):
    tenant = Tenant(slug="acme", name="Acme")
    db_session.add(tenant)
    db_session.flush()
    group = Group(tenant_id=tenant.id, name="eng")
    user = User(tenant_id=tenant.id, email="alice@acme.test", display_name="Alice")
    db_session.add_all([group, user])
    db_session.flush()
    source = Source(
        tenant_id=tenant.id,
        kind="local_fs",
        name="docs",
        config={
            "root": str(tmp_path),
            "allowed_group_ids": [str(group.id)],
            "allowed_user_ids": [str(user.id)],
        },
    )
    db_session.add(source)
    db_session.flush()
    (tmp_path / "a.md").write_text("# Alpha\n\nAlpha body text.", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Beta\n\nBeta body text.", encoding="utf-8")
    db_session.commit()
    return {"tenant": tenant, "group": group, "user": user, "source": source, "root": tmp_path}


def sync(db_session, world):
    return run_source_sync(db_session, world["tenant"].id, world["source"].id)


def test_each_chunk_carries_tenant_acl_and_vector(db_session, world):
    report = sync(db_session, world)
    client = FakeOpenSearch()
    count = apply_sync_report(
        db_session, client, FakeEmbedder(dimension=64), INDEX,
        world["tenant"].id, world["source"].id, report.upserted_ids, report.deleted_ids,
    )

    assert count == 2 and len(client.indexed) == 2
    _, _, body = client.indexed[0]
    assert set(body) == {
        "chunk_id", "tenant_id", "document_id", "source_id",
        "title", "content", "allowed_groups", "allowed_users", "embedding",
    }
    assert body["tenant_id"] == str(world["tenant"].id)
    assert body["allowed_groups"] == [str(world["group"].id)]
    assert body["allowed_users"] == [str(world["user"].id)]
    assert len(body["embedding"]) == 64


def test_deleted_document_is_removed_from_index(db_session, world):
    sync(db_session, world)
    (world["root"] / "b.md").unlink()
    report = sync(db_session, world)
    client = FakeOpenSearch()

    apply_sync_report(
        db_session, client, FakeEmbedder(), INDEX,
        world["tenant"].id, world["source"].id, report.upserted_ids, report.deleted_ids,
    )

    assert report.deleted_ids == ["b.md"]
    assert client.indexed == []
    filters = client.deleted[-1][1]["query"]["bool"]["filter"]
    assert {"term": {"tenant_id": str(world["tenant"].id)}} in filters


def test_indexer_refuses_document_from_another_tenant(db_session, world):
    sync(db_session, world)
    doc = db_session.execute(select(Document)).scalars().first()
    other = Tenant(slug="globex", name="Globex")
    db_session.add(other)
    db_session.flush()
    client = FakeOpenSearch()

    count = index_document(db_session, client, FakeEmbedder(), INDEX, other.id, doc.id)

    assert count == 0
    assert client.indexed == []
    filters = client.deleted[-1][1]["query"]["bool"]["filter"]
    assert filters[0] == {"term": {"tenant_id": str(other.id)}}