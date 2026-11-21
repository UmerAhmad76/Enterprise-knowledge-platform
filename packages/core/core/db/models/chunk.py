"""Chunks (text pieces) and embedding versions (which vector index is valid for which model)."""
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from core.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EmbeddingVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ek embedding model ka version aur uska OpenSearch index. Re-embedding ke liye naya row."""

    __tablename__ = "embedding_versions"
    __table_args__ = (
        UniqueConstraint("model_name", "model_version", name="uq_embedding_versions_model"),
        CheckConstraint("status IN ('building', 'active', 'retired')", name="ck_embedding_versions_status"),
    )

    model_name: Mapped[str] = mapped_column(String(128))  # e.g. bge-m3
    model_version: Mapped[str] = mapped_column(String(32))  # e.g. v1
    dimension: Mapped[int] = mapped_column(Integer)  # vector size, index mapping se match honi chahiye
    status: Mapped[str] = mapped_column(String(16), default="building")
    index_name: Mapped[str] = mapped_column(String(255), unique=True)  # OpenSearch index ka naam


class Chunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Document version ka ek tukra. Iska ID OpenSearch document ID ke taur pe bhi use hota hai."""

    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_version_id", "chunk_index", name="uq_chunks_version_index"),
        Index("ix_chunks_tenant_document", "tenant_id", "document_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE")
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE")
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_versions.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)