"""Source connectors, documents, their versions, and the ACL entries that guard them."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from core.db.models.base import Base, JSONType, TimestampMixin, UUIDPrimaryKeyMixin


class Source(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ek connection jaise Confluence space ya Jira project. Sync cursor yahin store hota hai."""

    __tablename__ = "sources"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))  # confluence | jira | gdrive | sql
    name: Mapped[str] = mapped_column(String(255))
    config: Mapped[dict] = mapped_column(JSONType, default=dict)  # secrets raw nahi, vault ref
    sync_cursor: Mapped[str | None] = mapped_column(String(512))  # incremental sync checkpoint
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Source system ka ek document. Latest state yahan, purani states DocumentVersion mein."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_id", "external_id", name="uq_documents_source_external"),
        CheckConstraint("status IN ('active', 'deleted', 'failed')", name="ck_documents_status"),
        Index("ix_documents_tenant_source", "tenant_id", "source_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE")
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sources.id", ondelete="CASCADE")
    )
    external_id: Mapped[str] = mapped_column(String(512))  # source system mein document ki ID
    title: Mapped[str] = mapped_column(String(1024))
    content_hash: Mapped[str] = mapped_column(String(64))  # sha256, incremental sync isse compare karta hai
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active")
    acl_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # ACL drift monitor


class DocumentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Har content change ka snapshot. Raw file S3/MinIO mein, yahan sirf reference hai."""

    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_no", name="uq_document_versions_doc_no"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    version_no: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(1024))  # S3/MinIO object key


class DocumentACL(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ek document par ek allowed principal. Principal user ya group ho sakta hai."""

    __tablename__ = "document_acl"
    __table_args__ = (
        UniqueConstraint("document_id", "principal_type", "principal_id", name="uq_document_acl_entry"),
        CheckConstraint("principal_type IN ('user', 'group')", name="ck_document_acl_principal_type"),
        # ACL lookup "is user/group ko kaunse documents allowed hain?" ke liye
        Index("ix_document_acl_principal", "tenant_id", "principal_type", "principal_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE")
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    principal_type: Mapped[str] = mapped_column(String(8))  # 'user' | 'group'
    # Polymorphic FK: DB level pe enforce nahi hoti, service layer validate karegi
    principal_id: Mapped[uuid.UUID] = mapped_column(Uuid)