"""Chat ki dependencies: embedder, search, reranker aur LLM. Settings se bante hain, aur tests inhe override kar sakte hain."""
from dataclasses import dataclass
from functools import lru_cache

from app.config import Settings, get_settings
from core.embeddings.base import Embedder
from core.embeddings.fake import FakeEmbedder
from core.llm.base import LLM
from core.llm.fake import FakeLLM
from core.retrieval.pipeline import SearchFn
from core.retrieval.reranker import NoopReranker, Reranker
from core.search_index.client import make_opensearch_client
from core.search_index.index_manager import ACTIVE_ALIAS
from core.search_index.search import make_search


@dataclass(frozen=True)
class ChatServices:
    """Ek jagah sab dependencies: route sirf ye object leta hai."""

    embedder: Embedder
    search: SearchFn
    llm: LLM
    reranker: Reranker


@lru_cache
def get_chat_services() -> ChatServices:
    """Pehli call par banta hai, phir same object milta hai. OpenSearch client yahin ek dafa banta hai."""
    settings = get_settings()
    client = make_opensearch_client(settings.opensearch_url)
    return ChatServices(
        embedder=_build_embedder(settings),
        search=make_search(client, index=ACTIVE_ALIAS),
        llm=_build_llm(settings),
        reranker=NoopReranker(),
    )


def _build_embedder(settings: Settings) -> Embedder:
    """Embedder bhi LLM ki tarah settings se banta hai, taake dono provider ek saath badlein aur mismatch na ho."""
    if settings.embedding_provider == "fake":
        return FakeEmbedder(dimension=settings.embedding_dimension)
    raise RuntimeError(
        f"EMBEDDING_PROVIDER={settings.embedding_provider!r} not implemented yet. "
        "Only 'fake' is available until a real embedder (e.g. bge) is wired in."
    )


def _build_llm(settings: Settings) -> LLM:
    """Provider ke hisaab se LLM banata hai. Anthropic ke liye key lazmi hai, warna startup par hi error."""
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty")
        from core.llm.providers.anthropic_llm import AnthropicLLM

        return AnthropicLLM(api_key=settings.anthropic_api_key, model=settings.llm_model)
    return FakeLLM(reply="Fake answer [1].")