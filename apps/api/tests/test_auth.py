"""Auth tests: protected routes reject missing, forged, and expired tokens; valid tokens round-trip."""
import uuid

import jwt
from fastapi.testclient import TestClient

from app.auth import create_access_token, decode_token
from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_me_without_token_is_401():
    assert client.get("/me").status_code == 401


def test_malformed_token_is_401():
    r = client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_alg_none_forged_token_is_401():
    # Attacker signature ke bina token banata hai. Algorithm pin hone ki wajah se ye reject hona chahiye.
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "tenant": str(uuid.uuid4())}, key=None, algorithm="none"
    )
    r = client.get("/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_expired_token_is_rejected():
    token = create_access_token(uuid.uuid4(), uuid.uuid4(), expires_minutes=-1)
    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_round_trip_keeps_identity():
    user_id, tenant_id = uuid.uuid4(), uuid.uuid4()
    ctx = decode_token(create_access_token(user_id, tenant_id))
    assert ctx.user_id == user_id
    assert ctx.tenant_id == tenant_id


def test_dev_token_is_hidden_outside_dev(monkeypatch):
    # Production simulate: environment prod hone par login route 404 de
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "prod")
    get_settings.cache_clear()
    try:
        r = client.post("/auth/dev-token", json={"tenant_slug": "acme", "email": "a@b.c"})
        assert r.status_code == 404
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()