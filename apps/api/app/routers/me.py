"""Identity endpoint: returns who the caller is and which groups they belong to."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_principals
from app.schemas.auth import MeResponse
from core.acl.principals import Principals
from core.db.models import User

router = APIRouter(tags=["identity"])


@router.get("/me", response_model=MeResponse)
def get_me(
    principals: Principals = Depends(get_principals),
    db: Session = Depends(get_db),
) -> MeResponse:
    """Token wale user ki profile aur ACL groups. Frontend ke liye context ka source."""
    user = db.get(User, principals.user_id)
    return MeResponse(
        user_id=principals.user_id,
        tenant_id=principals.tenant_id,
        email=user.email,
        display_name=user.display_name,
        group_ids=sorted(principals.group_ids),
    )