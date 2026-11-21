"""Feedback route tests: auth lazmi, rating validation, service ka 'not found' 404 mein badalna, aur successful vote."""
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.dependencies import get_principals
from app.main import app
from core.acl.principals import Principals
from core.common.errors import NotFoundError

client = TestClient(app)
TENANT = uuid.uuid4()
USER = uuid.uuid4()
KNOWN_QUERY = uuid.uuid4()
UNKNOWN_QUERY = uuid.uuid4()


@pytest.fixture
def wired(monkeypatch):
    def fake_record(db, tenant_id, user_id, query_id, rating, comment=None):
        if query_id == UNKNOWN_QUERY:
            raise NotFoundError("query not found")
        return SimpleNamespace(rating=rating)

    monkeypatch.setattr("app.routers.feedback.record_feedback", fake_record)
    app.dependency_overrides[get_principals] = lambda: Principals(
        user_id=USER, tenant_id=TENANT, group_ids=frozenset()
    )
    app.dependency_overrides[get_db] = lambda: object()
    yield
    app.dependency_overrides.clear()


def test_feedback_without_token_is_401():
    response = client.post("/feedback", json={"query_id": str(KNOWN_QUERY), "rating": 1})
    assert response.status_code == 401


def test_rating_zero_is_rejected(wired):
    response = client.post("/feedback", json={"query_id": str(KNOWN_QUERY), "rating": 0})
    assert response.status_code == 422


def test_valid_vote_returns_confirmation(wired):
    response = client.post("/feedback", json={"query_id": str(KNOWN_QUERY), "rating": -1})
    assert response.status_code == 200
    assert response.json() == {"query_id": str(KNOWN_QUERY), "rating": -1}


def test_unknown_or_foreign_query_is_404(wired):
    response = client.post("/feedback", json={"query_id": str(UNKNOWN_QUERY), "rating": 1})
    assert response.status_code == 404