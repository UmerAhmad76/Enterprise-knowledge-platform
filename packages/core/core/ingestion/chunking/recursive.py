"""Paragraph-aware chunker: poore paragraphs pack karta hai, sirf bade paragraphs ko todta hai."""
import re

from core.ingestion.types import TextChunk

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def chunk_text(text: str, max_tokens: int = 200, overlap_tokens: int = 30) -> list[TextChunk]:
    """Token count yahan words se approximate hai. Production mein model ka tokenizer use hoga."""
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if not 0 <= overlap_tokens < max_tokens:
        raise ValueError("overlap_tokens must be >= 0 and smaller than max_tokens")

    chunks: list[list[str]] = []
    current: list[str] = []

    for words in _paragraphs(text):
        if len(words) > max_tokens:
            # Bada paragraph: pehle jo jama hai woh flush karo, phir sliding windows banao
            if current:
                chunks.append(current)
                current = []
            chunks.extend(_windows(words, max_tokens, overlap_tokens))
            continue

        if current and len(current) + len(words) > max_tokens:
            chunks.append(current)
            carry = current[-overlap_tokens:] if overlap_tokens else []
            # Overlap + naya paragraph limit se bada ho to overlap chhod do
            current = carry if len(carry) + len(words) <= max_tokens else []
        current = current + words

    if current:
        chunks.append(current)

    return [
        TextChunk(index=i, text=" ".join(words), token_count=len(words))
        for i, words in enumerate(chunks)
    ]


def _paragraphs(text: str) -> list[list[str]]:
    """Blank lines par paragraphs todta hai, aur har paragraph ke words ki list banata hai."""
    return [p.split() for p in _PARAGRAPH_BREAK.split(text.strip()) if p.strip()]


def _windows(words: list[str], max_tokens: int, overlap_tokens: int) -> list[list[str]]:
    """Bade paragraph ke liye overlapping windows. Har window ke aakhri words agle window ke shuru mein aate hen."""
    step = max_tokens - overlap_tokens
    windows = []
    start = 0
    while True:
        windows.append(words[start : start + max_tokens])
        if start + max_tokens >= len(words):
            break
        start += step
    return windows