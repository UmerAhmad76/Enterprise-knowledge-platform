"""Plain data objects passed between connectors, parsers, chunkers and the sync pipeline."""
import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawDocument:
    """Document jaisa source ne diya: raw bytes aur wo ACL jo source ke hisaab se lagta hai."""

    external_id: str
    title: str
    content: bytes
    content_type: str
    allowed_group_ids: frozenset[uuid.UUID] = field(default_factory=frozenset)
    allowed_user_ids: frozenset[uuid.UUID] = field(default_factory=frozenset)


@dataclass(frozen=True)
class ParsedDocument:
    """RawDocument se nikla saaf text. Parser ye banata hai, chunker ise use karta hai."""

    title: str
    text: str


@dataclass(frozen=True)
class TextChunk:
    """Document ka ek tukda, embedding ke liye sized. index se original order maloom rehta hai."""

    index: int
    text: str
    token_count: int