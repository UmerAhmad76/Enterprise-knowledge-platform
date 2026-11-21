"""JWT creation and verification, plus the dependency that yields the verified identity."""
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    """Verified identity from a valid token. Tenant yahan se aata hai, header se nahi."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID, expires_minutes: int = 60) -> str:
    """Signed token banata hai. Dev login aur tests dono isi function ko use karte hen."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tenant": str(tenant_id),
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> AuthContext:
    """Verify karta hai: signature, expiry, aur algorithm. Koi bhi fault ho to 401."""
    settings = get_settings()
    try:
        # algorithms list pin hai: "alg: none" ya algorithm confusion attacks block hote hen
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return AuthContext(user_id=uuid.UUID(payload["sub"]), tenant_id=uuid.UUID(payload["tenant"]))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=401,
            detail="invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    """FastAPI dependency: har protected route ke liye Authorization header check karta hai."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)