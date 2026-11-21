"""Declarative base, shared column mixins, and cross-database type helpers."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Parent of every ORM model. Alembic reads Base.metadata to detect schema changes."""


# JSONB on Postgres (indexable, binary), plain JSON on other DBs (used by SQLite tests)
JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp. Naive datetime.now() multi-region systems mein bug banta hai."""
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    """UUID primary key Python mein generate hoti hai, taake INSERT se pehle ID mil jaye."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """created_at aur updated_at, audit ke liye har table mein."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )