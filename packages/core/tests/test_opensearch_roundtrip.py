"""Real OpenSearch test: pre-filter sach mein kaam karta hai ya nahi. Sirf Docker wale PC par chalta hai."""
import os
import uuid

import pytest

from core.acl.principals import Principals
from core.embeddings.fake import FakeEmbedder
from core.retrieval.pipeline import retrieve
from core.search_index.client import make_opensearch_client
from core.search_index.mappings.chunks_v1 import chunks_index_body
from core.search_index.search import make_search

OS_URL = os.environ.get("OPENSEARCH_URL")
pytestmark = pytest.mark.skipif(not OS_URL, reason="OPENSEARCH_URL set nahi, Docker stack chalao")

INDEX = "chunks-it-test"  # alias nahi, alag index: dev data ko touch nahi karta
TENANT = uuid.uuid4()
OTHER_TENANT = uuid.uuid4()
ENG = uuid.uuid4()
HR = uuid.uuid4()


@pytest.fixture(scope="module")
def client():
    c = make_opensearch_client(OS_URL)
    c.indices.delete(index=INDEX, ignore_unavailable=True)
    c.indices.create(index=INDEX, body=chunks_index_body(64))
    yield c
    c.indices.delete(index=INDEX, ignore_unavailable=True)


@pytest.fixture(scope="module")
def seeded(client):
    emb = FakeEmbedder(dimension=64)
    rows = [
        ("eng-leave", TENANT, "annual leave policy gives twenty days", [str(ENG)]),
        ("hr-salary", TENANT, "salary review schedule for managers", [str(HR)]),
        ("other-leave", OTHER_TENANT, "leave policy for another company", [str(ENG)]),
    ]
    for chunk_id, tenant, text, groups in rows:
        client.index(
            index=INDEX,
            id=chunk_id,
            body={
                "chunk_id": chunk_id,
                "tenant_id": str(tenant),
                "document_id": chunk_id,
                "source_id": "src",
                "title": chunk_id,
                "content": text,
                "allowed_groups": groups,
                "allowed_users": [],
                "embedding": emb.embed_documents([text])[0],
            },
            refresh=False,
        )
    client.indices.refresh(index=INDEX)


def ids_for(principals, seeded_client):
    search = make_search(seeded_client, INDEX)
    results = retrieve("leave policy", principals, FakeEmbedder(dimension=64), search, top_k=10)
    return {r.chunk_id for r in results}


def test_eng_user_sees_only_own_tenant_and_group(client, seeded):
    p = Principals(user_id=uuid.uuid4(), tenant_id=TENANT, group_ids=frozenset({ENG}))
    assert ids_for(p, client) == {"eng-leave"}


def test_hr_user_never_sees_eng_chunk(client, seeded):
    p = Principals(user_id=uuid.uuid4(), tenant_id=TENANT, group_ids=frozenset({HR}))
    ids = ids_for(p, client)
    assert "eng-leave" not in ids
    assert "other-leave" not in ids
    assert ids <= {"hr-salary"}


def test_stranger_from_other_tenant_sees_nothing(client, seeded):
    p = Principals(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), group_ids=frozenset({ENG}))
    assert ids_for(p, client) == set()