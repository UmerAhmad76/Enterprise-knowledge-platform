"""Chat queries and user feedback. This data feeds the eval suite (Risk 4: golden dataset)."""
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from core.db.models.base import Base, JSONType, TimestampMixin, UUIDPrimaryKeyMixin


class ChatQuery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ek user ka sawal, system ka jawab aur kaunse chunks use hue. Har retrieval ka audit trail."""

    __tablename__ = "chat_queries"
    __table_args__ = (Index("ix_chat_queries_tenant_created", "tenant_id", "created_at"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    retrieved_chunk_ids: Mapped[list[str]] = mapped_column(JSONType, default=list)
    embedding_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("embedding_versions.id", ondelete="SET NULL"), nullable=True
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer)


class Feedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User ka thumbs up/down. Ek user ek query par ek hi feedback de sakta hai."""

    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint("query_id", "user_id", name="uq_feedback_query_user"),
        CheckConstraint("rating IN (-1, 1)", name="ck_feedback_rating"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE")
    )
    query_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_queries.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE")
    )
    rating: Mapped[int] = mapped_column(Integer)  # -1 = galat, 1 = sahi
    comment: Mapped[str | None] = mapped_column(Text)