"""Deterministic fake embedder: model download ke bagair tests chalane ke liye. Production mein use nahi hota."""
import hashlib
import math

from core.embeddings.base import Embedder


class FakeEmbedder(Embedder):
    """Same text hamesha same vector deta hai, aur similar words ka overlap similarity banata hai."""

    model_name = "fake-hash"
    model_version = "v1"

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        """Har word ko hash karke vector ke ek slot mein add karta hai, phir normalise karta hai."""
        vec = [0.0] * self.dimension
        for word in text.lower().split():
            digest = hashlib.sha256(word.encode()).digest()
            slot = int.from_bytes(digest[:4], "big") % self.dimension
            vec[slot] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm else vec