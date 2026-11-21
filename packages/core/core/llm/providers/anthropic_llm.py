"""Claude provider. Anthropic SDK sirf is class ke andar import hota hai, taake bina key ke tests chal sakein."""
from core.llm.base import LLM


class AnthropicLLM(LLM):
    """Anthropic Messages API ka wrapper. Model ka naam settings se aata hai, code mein hardcode nahi."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5") -> None:
        from anthropic import Anthropic  # lazy import: SDK sirf tab chahiye jab provider anthropic ho

        self.model_name = model
        self._client = Anthropic(api_key=api_key)

    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        response = self._client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")