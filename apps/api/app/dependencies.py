"""Request-scoped dependencies: verified identity, resolved ACL principals, and the active embedding version."""
import uuid

from core.acl.principals import Principals, resolve_principals
from core.common.errors import AccessDeniedError, NotFoundError
from core.db.models import EmbeddingVersion
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context
from app.db import get_db
from app.services import ChatServices, get_chat_services


def get_principals(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Principals:
    """Token wale user ki ACL identity DB se nikalta hai. Ye har protected route ka base dependency hai."""
    try:
        return resolve_principals(db, auth.tenant_id, auth.user_id)
    except NotFoundError as exc:
        # Token valid hai lekin user database mein nahi (deleted ya cross-tenant)
        raise HTTPException(status_code=401, detail="token subject not found") from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=403, detail="user is inactive") from exc


def get_embedding_version_id(
    db: Session = Depends(get_db),
    services: ChatServices = Depends(get_chat_services),
) -> uuid.UUID | None:
    """Jo embedder abhi use ho raha hai, uski EmbeddingVersion row ka ID. Index banne se pehle None hota hai."""
    return db.execute(
        select(EmbeddingVersion.id).where(
            EmbeddingVersion.model_name == services.embedder.model_name,
            EmbeddingVersion.model_version == services.embedder.model_version,
        )
    ).scalar_one_or_none()