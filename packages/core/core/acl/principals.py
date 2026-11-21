"""Resolves who a user is for ACL purposes: their user ID plus every group they belong to."""
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.common.errors import AccessDeniedError, NotFoundError
from core.db.models import Group, User, user_groups


@dataclass(frozen=True)
class Principals:
    """Immutable identity snapshot used by every retrieval query in this request."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    group_ids: frozenset[uuid.UUID] = field(default_factory=frozenset)


def resolve_principals(session: Session, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Principals:
    """Loads the user, checks tenant ownership and active status, then collects group memberships."""
    user = session.get(User, user_id)
    # Cross-tenant ya missing user ko ek hi error: data ke wajood ka pata nahi chalna chahiye
    if user is None or user.tenant_id != tenant_id:
        raise NotFoundError("user not found")
    if not user.is_active:
        raise AccessDeniedError("user is inactive")

    # Join Group par tenant filter: defense in depth, agar membership data corrupt ho to bhi
    group_rows = session.execute(
        select(user_groups.c.group_id)
        .join(Group, Group.id == user_groups.c.group_id)
        .where(user_groups.c.user_id == user_id, Group.tenant_id == tenant_id)
    ).scalars().all()

    return Principals(user_id=user_id, tenant_id=tenant_id, group_ids=frozenset(group_rows))