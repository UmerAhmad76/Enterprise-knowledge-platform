"""Chat route tests: auth lazmi, validation, ACL search tak pahunchta hai, citations sahi, audit row, aur LLM failure handling."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.dependencies import get_principals
from app.main import app
from app.services import ChatServices, get_chat_services
from core.acl.principals import Principals
from core.embeddings.fake import FakeEmbedder
from core.generation.answer import NO_SOURCES_TEXT
from core.llm.base import LLM
from core.llm.fake import FakeLLM
from core.retrieval.reranker import NoopReranker

client = TestClient(app)
TENANT = uuid.uuid4()
USER = uuid.uuid4()


class FakeSession:
    """Database ki jagah: add aur commit record karta hai, taake audit row check ho sake."""

    def __init__(self) -> None:
        self.added: list = []
        self.committed = False

    def add(self, obj) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        self.committed = True


class BrokenLLM(LLM):
    """Har call par exception deta hai, taake provider-down scenario simulate ho."""

    model_name = "broken-llm"

    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        raise RuntimeError("provider is down")


def hit(chunk_id: str, document_id: str, title: str, content: str) -> dict:
    return {"_source": {"chunk_id": chunk_id, "document_id": document_id, "title": title, "content": content}}


@pytest.fixture
def wired():
    session = FakeSession()
    search_calls: list[dict] = []
    llm = FakeLLM(reply="Employees get 20 days [1].")

    def search(body: dict) -> list[dict]:
        search_calls.append(body)
        return [
            hit("c1", "d1", "Leave Policy", "Employees get 20 days."),
            hit("c2", "d2", "Salary", "Reviews happen in March."),
        ]

    app.dependency_overrides[get_principals] = lambda: Principals(
        user_id=USER, tenant_id=TENANT, group_ids=frozenset()
    )
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_chat_services] = lambda: ChatServices(
        embedder=FakeEmbedder(64), search=search, llm=llm, reranker=NoopReranker()
    )
    yield {"session": session, "search_calls": search_calls, "llm": llm, "search_fn": search}
    app.dependency_overrides.clear()


def test_chat_without_token_is_401():
    response = client.post("/chat", json={"question": "leave?"})
    assert response.status_code == 401


def test_blank_question_is_rejected(wired):
    response = client.post("/chat", json={"question": "   "})
    assert response.status_code == 422


def test_answer_has_citations_and_search_is_tenant_scoped(wired):
    response = client.post("/chat", json={"question": "How many leave days?"})
    assert response.status_code == 200

    body = response.json()
    assert body["answer"] == "Employees get 20 days [1]."
    assert body["citations"][0]["chunk_id"] == "c1"
    assert body["citations"][0]["title"] == "Leave Policy"
    assert body["invalid_citation_numbers"] == []
    assert all(str(TENANT) in str(call["query"]) for call in wired["search_calls"])


def test_chat_writes_one_audit_row(wired):
    client.post("/chat", json={"question": "How many leave days?"})

    session = wired["session"]
    assert session.committed is True
    assert len(session.added) == 1
    row = session.added[0]
    assert row.question == "How many leave days?"
    assert row.retrieved_chunk_ids == ["c1", "c2"]
    assert row.answer == "Employees get 20 days [1]."


def test_no_hits_returns_fixed_message_and_skips_llm(wired):
    app.dependency_overrides[get_chat_services] = lambda: ChatServices(
        embedder=FakeEmbedder(64), search=lambda body: [], llm=wired["llm"], reranker=NoopReranker()
    )

    response = client.post("/chat", json={"question": "anything"})
    assert response.json()["answer"] == NO_SOURCES_TEXT
    assert wired["llm"].calls == []


def test_llm_failure_returns_503_and_still_saves_audit_row(wired):
    app.dependency_overrides[get_chat_services] = lambda: ChatServices(
        embedder=FakeEmbedder(64), search=wired["search_fn"], llm=BrokenLLM(), reranker=NoopReranker()
    )

    response = client.post("/chat", json={"question": "How many leave days?"})

    assert response.status_code == 503
    session = wired["session"]
    assert session.committed is True
    assert len(session.added) == 1
    row = session.added[0]
    assert row.answer is None
    assert row.retrieved_chunk_ids == ["c1", "c2"]


def test_search_failure_returns_503_without_audit_row(wired):
    def broken_search(body: dict):
        raise RuntimeError("opensearch unreachable")

    app.dependency_overrides[get_chat_services] = lambda: ChatServices(
        embedder=FakeEmbedder(64), search=broken_search, llm=wired["llm"], reranker=NoopReranker()
    )

    response = client.post("/chat", json={"question": "How many leave days?"})

    assert response.status_code == 503
    assert wired["session"].committed is False