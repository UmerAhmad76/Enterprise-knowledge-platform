"""Security tests: asli JWT, asli DB principals (har request par), aur ACL filter. Docker ki zaroorat nahi."""
import uuid

import jwt

from core.db.models import ChatQuery, User
from tests.support import bearer

TENANT_OF = {"alice": "acme", "bob": "acme", "eve": "globex"}


def headers_for(world, who: str) -> dict:
    return bearer(world[who], world[TENANT_OF[who]])


def ask(client, world, who: str, question: str = "annual leave", extra: dict | None = None):
    body = {"question": question, **(extra or {})}
    return client.post("/chat", json=body, headers=headers_for(world, who))


def retrieved(world, response) -> set[str]:
    """Audit row se wo chunk IDs jo is jawab ke liye retrieve hue."""
    with world["SessionLocal"]() as s:
        row = s.get(ChatQuery, uuid.UUID(response.json()["query_id"]))
        return set(row.retrieved_chunk_ids)


def test_each_user_sees_exactly_their_visible_chunks(client, world):
    expected = {
        "alice": {"c-leave", "c-onboard"},
        "bob": {"c-salary"},
        "eve": {"c-globex"},
    }
    for who, visible in expected.items():
        response = ask(client, world, who)
        assert response.status_code == 200, response.text
        assert retrieved(world, response) == visible, who


def test_citations_never_reference_hidden_documents(client, world):
    response = ask(client, world, "alice", question="salary reviews")
    titles = {c["title"] for c in response.json()["citations"]}
    assert titles <= {"Leave Policy", "Onboarding Guide"}


def test_exact_title_of_hidden_document_does_not_leak(client, world):
    response = ask(client, world, "alice", question="Salary Reviews")
    assert "c-salary" not in retrieved(world, response)


def test_removing_group_takes_effect_on_next_request(client, world):
    first = ask(client, world, "alice")
    assert "c-leave" in retrieved(world, first)

    # Token wahi rehta hai. Sirf DB mein membership hati hai.
    with world["SessionLocal"]() as s:
        s.get(User, world["alice"]).groups = []
        s.commit()

    second = ask(client, world, "alice")
    assert second.status_code == 200
    assert retrieved(world, second) == set()


def test_deactivated_user_is_blocked_on_next_request(client, world):
    with world["SessionLocal"]() as s:
        s.get(User, world["alice"]).is_active = False
        s.commit()

    response = ask(client, world, "alice")
    assert response.status_code == 403


def test_user_id_with_other_tenant_claim_is_rejected(client, world):
    response = client.post(
        "/chat",
        json={"question": "annual leave"},
        headers=bearer(world["alice"], world["globex"]),
    )
    assert response.status_code == 401


def test_token_signed_with_other_secret_is_rejected(client, world):
    forged = jwt.encode(
        {"sub": str(world["alice"]), "tenant": str(world["acme"]), "exp": 9999999999},
        "attacker-secret-0123456789abcdef0123",
        algorithm="HS256",
    )
    response = client.post(
        "/chat",
        json={"question": "annual leave"},
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert response.status_code == 401


def test_tenant_in_request_body_is_ignored(client, world):
    response = ask(client, world, "alice", extra={"tenant_id": str(world["globex"])})
    assert response.status_code == 200
    chunks = retrieved(world, response)
    assert "c-leave" in chunks
    assert "c-globex" not in chunks


def test_other_tenant_cannot_vote_on_query(client, world):
    response = ask(client, world, "alice")
    query_id = response.json()["query_id"]

    attack = client.post(
        "/feedback",
        json={"query_id": query_id, "rating": 1},
        headers=headers_for(world, "eve"),
    )
    assert attack.status_code == 404


def test_audit_row_records_callers_tenant_and_user(client, world):
    response = ask(client, world, "alice")
    with world["SessionLocal"]() as s:
        row = s.get(ChatQuery, uuid.UUID(response.json()["query_id"]))
        assert row.tenant_id == world["acme"]
        assert row.user_id == world["alice"]