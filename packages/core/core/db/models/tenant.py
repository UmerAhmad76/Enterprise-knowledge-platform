"""Tenant: the top-level isolation boundary. Every business row carries a tenant_id."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ek row ek customer organisation ko represent karti hai."""

    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)