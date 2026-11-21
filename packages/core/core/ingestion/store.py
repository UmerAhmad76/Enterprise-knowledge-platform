"""Storage contract jis par pipeline depend karta hai. Abhi SQL implementation hai, baad mein OpenSearch sink bhi."""
from typing import Protocol

from core.ingestion.types import RawDocument, TextChunk


class DocumentStore(Protocol):
    """Pipeline sirf ye methods jaanta hai, is liye storage badalna asaan hai."""

    def known_hashes(self) -> dict[str, str]:
        """Is source ke active documents: external_id se content_hash ka map."""

    def upsert_document(
        self, raw: RawDocument, content_hash: str, title: str, chunks: list[TextChunk]
    ) -> None:
        """Document banao ya update karo, version badhao, chunks aur ACL replace karo."""

    def refresh_acl(self, raw: RawDocument) -> bool:
        """Sirf ACL update karo, version nahi badlo. Badla to True, same ho to False."""

    def mark_deleted(self, external_id: str) -> None:
        """Document source se gayab hai. Chunks hata do taake retrieval mein na aaye."""