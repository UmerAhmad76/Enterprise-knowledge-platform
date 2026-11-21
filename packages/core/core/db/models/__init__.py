"""Imports every model so Base.metadata is complete for Alembic and tests."""
from core.db.models.base import Base
from core.db.models.chunk import Chunk, EmbeddingVersion
from core.db.models.document import Document, DocumentACL, DocumentVersion, Source
from core.db.models.feedback import ChatQuery, Feedback
from core.db.models.tenant import Tenant
from core.db.models.user import Group, User, user_groups

__all__ = [
    "Base",
    "Tenant",
    "User",
    "Group",
    "user_groups",
    "Source",
    "Document",
    "DocumentVersion",
    "DocumentACL",
    "EmbeddingVersion",
    "Chunk",
    "ChatQuery",
    "Feedback",
]