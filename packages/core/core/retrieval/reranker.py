"""Reranker contract: top candidates ko query ke saath dobara score karta hai. Cross-encoder model isi ko implement karega."""
from abc import ABC, abstractmethod

from core.retrieval.types import RetrievedChunk


class Reranker(ABC):
    """Candidates ki list lo, better order mein top_k wapas do."""

    @abstractmethod
    def rerank(self, question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        """Query ke hisaab se chunks dobara order karo aur sirf top_k rakho."""


class NoopReranker(Reranker):
    """Default: koi reranking nahi, RRF ka order hi rehta hai."""

    def rerank(self, question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        return chunks[:top_k]