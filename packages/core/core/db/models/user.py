"""Users, groups and their membership. Groups are what document ACLs point at."""
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Table, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Many-to-many link between users and groups. Composite PK prevents duplicate memberships.
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Uuid, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    # Reverse lookup "is group ke members kaun hain?" ke liye index (ACL re-sync mein kaam aata hai)
    Index("ix_user_groups_group_id", "group_id"),
)


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Platform user. Email tenant ke andar unique hai, globally nahi."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(255))
    external_id: Mapped[str | None] = mapped_column(String(255))  # SSO (OIDC "sub") claim
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    groups: Mapped[list["Group"]] = relationship(secondary=user_groups, back_populates="members")


class Group(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Group, jaise 'eng', 'hr-managers'. Document ACL mein group ID store hoti hai."""

    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_groups_tenant_name"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))

    members: Mapped[list[User]] = relationship(secondary=user_groups, back_populates="groups")