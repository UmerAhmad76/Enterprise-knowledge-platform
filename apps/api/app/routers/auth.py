"""Auth routes. The dev-token login is compiled out of production by returning 404."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.config import get_settings
from app.db import get_db
from app.schemas.auth import DevTokenRequest, TokenResponse
from core.db.models import Tenant, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-token", response_model=TokenResponse)
def dev_token(body: DevTokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Local testing ke liye token deta hai. Non-dev environment mein endpoint exist hi nahi karta."""
    if get_settings().environment != "dev":
        raise HTTPException(status_code=404, detail="not found")

    tenant = db.execute(select(Tenant).where(Tenant.slug == body.tenant_slug)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    user = db.execute(
        select(User).where(User.tenant_id == tenant.id, User.email == body.email)
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail="user not found")

    return TokenResponse(access_token=create_access_token(user.id, tenant.id))