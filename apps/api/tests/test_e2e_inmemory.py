"""In-memory end-to-end test: asli auth, asli DB rows (SQLite), asli ACL filter aur asli routes. Sirf OpenSearch ki jagah fake index hai."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.db import get_db
from app.main import app
from app.services import ChatServices, get_chat_services
from core.db.models import Base, ChatQuery, Group, Tenant, User
from core.embeddings.fake import FakeEmbedder
from core.llm.fake import FakeLLM
from core.retrieval.reranker import NoopReranker

client = TestClient(app)


def matches(doc: dict, clause: dict) -> bool:
    """OpenSearch ke ACL filter ka chhota evaluator (bool, term, terms). Real OpenSearch ka asar copy karta hai."""
    if "bool" in clause:
        b = clause["bool"]
        ok = all(matches(doc, c) for c in b.get("filter", []) + b.get("must", []))
        if "should" in b:
            hits = sum(matches(doc, c) for c in b["should"])
            ok = ok and hits >= b.get("minimum_should_match", 1)
        return ok
    if "term" in clause:
        (field, value), = clause["term"].items()
        current = doc.get(field)
        return value in current if isinstance(current, list) else current == value
    if "terms" in clause:
        (field, values), = clause["terms"].items()
        return any(v in (doc.get(field) or []) for v in values)
    raise AssertionError(f"unsupported clause: {clause}")


def make_search(index: list[dict]):
    """Fake OpenSearch: har query ka ACL filter nikalta hai aur sirf matching documents wapas deta hai."""

    def search(body: dict) -> list[dict]:
        query = body["query"]
        acl_filter = query["knn"]["embedding"]["filter"] if "knn" in query else query["bool"]["filter"][0]
        return [
            {"_source": {k: doc[k] for k in ("chunk_id", "document_id", "title", "content")}}
            for doc in index
            if matches(doc, acl_filter)
        ]

    return search


def auth(user_id: uuid.UUID, tenant_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id, tenant_id)}"}


def retrieved_ids(world: dict, query_id: str) -> list[str]:
    with world["SessionLocal"]() as session:
        return session.get(ChatQuery, uuid.UUID(query_id)).retrieved_chunk_ids


@pytest.fixture
def world():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as s:
        tenant = Tenant(slug="acme", name="Acme")
        s.add(tenant)
        s.flush()
        eng = Group(tenant_id=tenant.id, name="eng")
        hr = Group(tenant_id=tenant.id, name="hr-managers")
        alice = User(tenant_id=tenant.id, email="alice@acme.test", display_name="Alice")
        bob = User(tenant_id=tenant.id, email="bob@acme.test", display_name="Bob")
        s.add_all([eng, hr, alice, bob])
        s.flush()
        alice.groups.append(eng)
        bob.groups.append(hr)
        s.commit()
        T, ENG, HR = str(tenant.id), str(eng.id), str(hr.id)
        tenant_id, alice_id, bob_id = tenant.id, alice.id, bob.id

    index = [
        {"chunk_id": "c-leave", "document_id": "d-leave", "title": "Leave Policy",
         "content": "Employees get twenty days of annual leave.", "tenant_id": T,
         "allowed_groups": [ENG], "allowed_users": []},
        {"chunk_id": "c-onboard", "document_id": "d-onboard", "title": "Onboarding Guide",
         "content": "New hires receive a laptop.", "tenant_id": T,
         "allowed_groups": [ENG], "allowed_users": []},
        {"chunk_id": "c-salary", "document_id": "d-salary", "title": "Salary Reviews",
         "content": "Salary reviews happen every March.", "tenant_id": T,
         "allowed_groups": [HR], "allowed_users": []},
    ]

    def db_override():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_chat_services] = lambda: ChatServices(
        embedder=FakeEmbedder(64),
        search=make_search(index),
        llm=FakeLLM(reply="Answer [1]."),
        reranker=NoopReranker(),
    )
    yield {
        "SessionLocal": SessionLocal,
        "tenant": tenant_id,
        "alice": alice_id,
        "bob": bob_id,
    }
    app.dependency_overrides.clear()


def test_alice_retrieves_only_eng_chunks(world):
    response = client.post("/chat", json={"question": "annual leave"}, headers=auth(world["alice"], world["tenant"]))
    assert response.status_code == 200
    assert set(retrieved_ids(world, response.json()["query_id"])) == {"c-leave", "c-onboard"}


def test_bob_retrieves_only_hr_chunks(world):
    response = client.post("/chat", json={"question": "salary reviews"}, headers=auth(world["bob"], world["tenant"]))
    assert response.status_code == 200
    assert set(retrieved_ids(world, response.json()["query_id"])) == {"c-salary"}


def test_feedback_is_owner_only_end_to_end(world):
    chat = client.post("/chat", json={"question": "annual leave"}, headers=auth(world["alice"], world["tenant"]))
    query_id = chat.json()["query_id"]

    stranger = client.post("/feedback", json={"query_id": query_id, "rating": -1}, headers=auth(world["bob"], world["tenant"]))
    assert stranger.status_code == 404

    owner = client.post("/feedback", json={"query_id": query_id, "rating": -1}, headers=auth(world["alice"], world["tenant"]))
    assert owner.status_code == 200