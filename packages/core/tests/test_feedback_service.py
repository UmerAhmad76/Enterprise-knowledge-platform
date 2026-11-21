"""Feedback service tests: owner vote de sakta hai, dobara vote update hota hai (comment ko mitaye bagair), aur doosre user ya tenant ko 'not found' milta hai."""
import pytest
from sqlalchemy import func, select

from core.common.errors import NotFoundError
from core.db.models import ChatQuery, Feedback, Tenant, User
from core.feedback.service import record_feedback


@pytest.fixture
def world(db_session):
    acme = Tenant(slug="acme", name="Acme")
    globex = Tenant(slug="globex", name="Globex")
    db_session.add_all([acme, globex])
    db_session.flush()
    alice = User(tenant_id=acme.id, email="alice@acme.test", display_name="Alice")
    bob = User(tenant_id=acme.id, email="bob@acme.test", display_name="Bob")
    eve = User(tenant_id=globex.id, email="eve@globex.test", display_name="Eve")
    db_session.add_all([alice, bob, eve])
    db_session.flush()
    query = ChatQuery(tenant_id=acme.id, user_id=alice.id, question="leave?", retrieved_chunk_ids=[])
    db_session.add(query)
    db_session.flush()
    return {"acme": acme, "globex": globex, "alice": alice, "bob": bob, "eve": eve, "query": query}


def test_owner_can_vote(db_session, world):
    row = record_feedback(db_session, world["acme"].id, world["alice"].id, world["query"].id, 1)
    assert row.rating == 1


def test_second_vote_updates_instead_of_duplicating(db_session, world):
    args = (db_session, world["acme"].id, world["alice"].id, world["query"].id)
    record_feedback(*args, 1)
    record_feedback(*args, -1, comment="wrong document")

    count = db_session.execute(select(func.count()).select_from(Feedback)).scalar_one()
    rating = db_session.execute(select(Feedback.rating)).scalar_one()
    assert count == 1
    assert rating == -1


def test_revoting_without_comment_keeps_previous_comment(db_session, world):
    args = (db_session, world["acme"].id, world["alice"].id, world["query"].id)
    record_feedback(*args, -1, comment="wrong document")
    # User apna mind badalta hai aur bina comment ke 👍 deta hai
    record_feedback(*args, 1)

    row = db_session.execute(select(Feedback)).scalar_one()
    assert row.rating == 1
    assert row.comment == "wrong document"


def test_explicit_empty_comment_clears_previous_comment(db_session, world):
    args = (db_session, world["acme"].id, world["alice"].id, world["query"].id)
    record_feedback(*args, -1, comment="wrong document")
    record_feedback(*args, -1, comment=None)

    row = db_session.execute(select(Feedback)).scalar_one()
    assert row.comment is None


def test_other_user_in_same_tenant_cannot_vote(db_session, world):
    with pytest.raises(NotFoundError):
        record_feedback(db_session, world["acme"].id, world["bob"].id, world["query"].id, 1)


def test_user_from_other_tenant_cannot_vote(db_session, world):
    with pytest.raises(NotFoundError):
        record_feedback(db_session, world["globex"].id, world["eve"].id, world["query"].id, 1)


def test_invalid_rating_is_rejected(db_session, world):
    with pytest.raises(ValueError):
        record_feedback(db_session, world["acme"].id, world["alice"].id, world["query"].id, 0)