"""Embedder contract: text ko vector mein badalne wala interface. Har model isi ko implement karta hai."""
from abc import ABC, abstractmethod


class Embedder(ABC):
    """Model name aur version bhi yahan hote hain, taake versioned index sahi chune."""

    model_name: str
    model_version: str
    dimension: int

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Chunks ke liye vectors. Ek text ka ek vector, aur order same rehta hai."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """User ke sawal ke liye vector. Kuch models documents aur queries mein alag prefix maangte hain."""