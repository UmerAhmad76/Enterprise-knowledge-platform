"""Request and response models for auth and identity endpoints."""
import uuid

from pydantic import BaseModel


class DevTokenRequest(BaseModel):
    """Dev login ka input: tenant slug aur email. Sirf dev environment mein kaam karta hai."""

    tenant_slug: str
    email: str


class TokenResponse(BaseModel):
    """Access token wrapper, OAuth2 style."""

    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    """Logged-in user ki identity aur groups. Frontend isi se user ka context leta hai."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    display_name: str
    group_ids: list[uuid.UUID]