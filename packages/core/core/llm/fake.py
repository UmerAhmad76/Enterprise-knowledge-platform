"""Test LLM: fixed jawab deta hai, taake generation ka code bina API key ke test ho sake."""
from core.llm.base import LLM


class FakeLLM(LLM):
    """Har call record karta hai, aur ek fixed reply return karta hai. Tests mein asli model ki jagah."""

    model_name = "fake-llm"

    def __init__(self, reply: str = "Fake answer [1].") -> None:
        self.reply = reply
        self.calls: list[dict[str, str]] = []

    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        self.calls.append({"system": system, "user": user})
        return self.reply