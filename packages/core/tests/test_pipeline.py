"""Pipeline test: fake search ke saath dono searches ACL se chalti hain aur fused result sahi aata hai."""
import uuid

from core.acl.principals import Principals
from core.embeddings.fake import FakeEmbedder
from core.retrieval.pipeline import retrieve


def hit(chunk_id: str, document_id: str) -> dict:
    return {"_source": {"chunk_id": chunk_id, "document_id": document_id}}


def test_retrieve_fuses_both_searches_and_keeps_acl_in_every_call():
    principals = Principals(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())
    calls: list[dict] = []

    def fake_search(body: dict) -> list[dict]:
        calls.append(body)
        if "multi_match" in str(body["query"]):
            return [hit("c1", "d1"), hit("c2", "d1"), hit("c3", "d2")]
        return [hit("c2", "d1"), hit("c4", "d3")]

    results = retrieve("leave policy", principals, FakeEmbedder(), fake_search, top_k=3)

    assert len(calls) == 2
    assert all(str(principals.tenant_id) in str(body["query"]) for body in calls)
    assert results[0].chunk_id == "c2"  # dono lists mein hai, sab se upar
    assert len(results) == 3
    assert all(r.document_id for r in results)


def test_no_hits_returns_empty_list():
    principals = Principals(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())
    results = retrieve("anything", principals, FakeEmbedder(), lambda body: [])
    assert results == []