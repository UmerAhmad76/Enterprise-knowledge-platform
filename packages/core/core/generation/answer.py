"""Poora answer flow: retrieved chunks ko numbered sources banao, LLM ko do, citations verify karo."""
from dataclasses import dataclass, field

from core.generation.citations import Citation, resolve_citations
from core.llm.base import LLM
from core.llm.prompts import DEFAULT_PROMPT_VERSION, PROMPTS


@dataclass(frozen=True)
class SourceChunk:
    """Retrieval se aaya ek chunk, uske text ke saath. Generation ko IDs ke ilawa text bhi chahiye."""

    chunk_id: str
    document_id: str
    title: str
    text: str


@dataclass(frozen=True)
class Answer:
    """Final jawab: text, citations jo sach mein use hue, aur invalid numbers (debug aur eval ke liye)."""

    text: str
    citations: list[Citation] = field(default_factory=list)
    invalid_citation_numbers: list[int] = field(default_factory=list)
    prompt_version: str = DEFAULT_PROMPT_VERSION
    model_name: str = ""


NO_SOURCES_TEXT = "I could not find this in the documents you have access to."


def generate_answer(
    question: str,
    chunks: list[SourceChunk],
    llm: LLM,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    max_tokens: int = 512,
) -> Answer:
    """Chunks khaali hon to LLM call hi nahi hota. Ye bhi ACL ka hissa hai: unauthorized text model ko nahi jata."""
    if not chunks:
        return Answer(text=NO_SOURCES_TEXT, prompt_version=prompt_version, model_name=llm.model_name)

    prompt = PROMPTS[prompt_version]
    numbered = {i: c for i, c in enumerate(chunks, start=1)}
    user_message = prompt.build_user_message(
        question, [(i, c.title, c.text) for i, c in numbered.items()]
    )
    raw = llm.complete(prompt.SYSTEM_PROMPT, user_message, max_tokens=max_tokens)

    citation_map = {
        i: Citation(number=i, chunk_id=c.chunk_id, document_id=c.document_id, title=c.title)
        for i, c in numbered.items()
    }
    used, invalid = resolve_citations(raw, citation_map)
    return Answer(
        text=raw.strip(),
        citations=used,
        invalid_citation_numbers=invalid,
        prompt_version=prompt_version,
        model_name=llm.model_name,
    )