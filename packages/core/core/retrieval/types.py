"""Retrieval ka output type. Alag file mein rakha hai taake reranker aur pipeline dono ise import kar sakein bina circular import ke."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    """Ek mila hua chunk: IDs, fused score, aur generation ke liye title aur text."""

    chunk_id: str
    document_id: str
    score: float
    title: str = ""
    text: str = ""