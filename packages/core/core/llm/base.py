"""LLM contract: prompt lo, text wapas do. Claude, OpenAI ya local model, sab isi ko implement karenge."""
from abc import ABC, abstractmethod


class LLM(ABC):
    """Model ka naam aur version bhi yahan hai, taake har jawab kis model se bana, ye record ho sake."""

    model_name: str

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        """System instructions aur user message lo, model ka text jawab return karo."""