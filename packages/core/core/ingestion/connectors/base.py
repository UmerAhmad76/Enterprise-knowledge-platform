"""Connector contract: har source (local files, Confluence, Jira) inhi do methods ko implement karta hai."""
from abc import ABC, abstractmethod

from core.ingestion.types import RawDocument


class Connector(ABC):
    """Source adapter. Source-specific API calls is class ke andar rehti hain, pipeline ke bahar."""

    kind: str

    @abstractmethod
    def list_document_ids(self) -> list[str]:
        """Source mein abhi maujood har document ka external ID return karo."""

    @abstractmethod
    def fetch(self, external_id: str) -> RawDocument:
        """Ek document download karo. Bad ID par ValueError, I/O problem par OSError."""