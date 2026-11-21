"""Metadata aur reranker tests: title/text search hits se aate hain, aur reranker order badal sakta hai."""
import uuid

from core.acl.principals import Principals
from core.embeddings.fake import FakeEmbedder
from core.retrieval.pipeline import retrieve
from core.retrieval.reranker import Reranker
from core.retrieval.types import RetrievedChunk


def hit(chunk_id: str, document_id: str, title: str, content: str) -> dict:
    return {"_source": {"chunk_id": chunk_id, "document_id": document_id, "title": title, "content": content}}


def make_search():
    def search(body: dict) -> list[dict]:
        if "multi_match" in str(body["query"]):
            return [hit("c1", "d1", "Leave", "twenty days"), hit("c2", "d2", "Salary", "march")]
        return [hit("c2", "d2", "Salary", "march")]

    return search


class ReverseReranker(Reranker):
    """Test ke liye: order ulta kar deta hai, taake dikhe ke reranker asar karta hai."""

    def rerank(self, question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        return list(reversed(chunks))[:top_k]


def principals() -> Principals:
    return Principals(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())


def test_title_and_text_come_from_search_hits():
    results = retrieve("leave", principals(), FakeEmbedder(), make_search(), top_k=5)
    by_id = {r.chunk_id: r for r in results}
    assert by_id["c1"].title == "Leave"
    assert by_id["c1"].text == "twenty days"


def test_reranker_can_change_the_order():
    base = retrieve("leave", principals(), FakeEmbedder(), make_search(), top_k=5)
    reranked = retrieve(
        "leave", principals(), FakeEmbedder(), make_search(), top_k=5, reranker=ReverseReranker()
    )
    assert [r.chunk_id for r in reranked] == list(reversed([r.chunk_id for r in base]))