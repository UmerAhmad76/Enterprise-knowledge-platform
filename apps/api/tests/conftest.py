"""Shared API fixtures: in-memory SQLite, do tenants, teen users, aur ACL-aware fake index. Routes ki dependencies overridden hain, lekin principals ka asli path chalta hai."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.services import ChatServices, get_chat_services
from core.db.models import Base, Group, Tenant, User
from core.embeddings.fake import FakeEmbedder
from core.llm.fake import FakeLLM
from core.retrieval.reranker import NoopReranker
from tests.support import make_search


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def world():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as s:
        acme = Tenant(slug="acme", name="Acme")
        globex = Tenant(slug="globex", name="Globex")
        s.add_all([acme, globex])
        s.flush()
        eng = Group(tenant_id=acme.id, name="eng")
        hr = Group(tenant_id=acme.id, name="hr-managers")
        globex_eng = Group(tenant_id=globex.id, name="eng")
        alice = User(tenant_id=acme.id, email="alice@acme.test", display_name="Alice")
        bob = User(tenant_id=acme.id, email="bob@acme.test", display_name="Bob")
        eve = User(tenant_id=globex.id, email="eve@globex.test", display_name="Eve")
        s.add_all([eng, hr, globex_eng, alice, bob, eve])
        s.flush()
        alice.groups.append(eng)
        bob.groups.append(hr)
        eve.groups.append(globex_eng)
        s.commit()

        ids = {
            "acme": acme.id, "globex": globex.id,
            "alice": alice.id, "bob": bob.id, "eve": eve.id,
        }
        T, G = str(acme.id), str(globex.id)
        ENG, HR, GENG = str(eng.id), str(hr.id), str(globex_eng.id)

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
        {"chunk_id": "c-globex", "document_id": "d-globex", "title": "Globex Leave",
         "content": "Globex staff get fifteen days.", "tenant_id": G,
         "allowed_groups": [GENG], "allowed_users": []},
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
    yield {"SessionLocal": SessionLocal, "index": index, **ids}
    app.dependency_overrides.clear()