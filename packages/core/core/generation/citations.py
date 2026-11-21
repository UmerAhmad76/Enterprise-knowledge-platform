"""Jawab mein [n] citations ko asli chunks se jorta hai, aur ghair maujood sources ko pakadta hai."""
import re
from dataclasses import dataclass

_CITATION = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True)
class Citation:
    """Ek source jo jawab mein use hua: number, chunk ID, document ID, aur title."""

    number: int
    chunk_id: str
    document_id: str
    title: str


def extract_citation_numbers(answer: str) -> list[int]:
    """Jawab mein jitne bhi [n] hain, unke numbers, pehli dafa aane ke order mein."""
    seen: list[int] = []
    for match in _CITATION.finditer(answer):
        number = int(match.group(1))
        if number not in seen:
            seen.append(number)
    return seen


def resolve_citations(answer: str, sources: dict[int, Citation]) -> tuple[list[Citation], list[int]]:
    """Valid citations aur invalid numbers alag karta hai. Invalid number ka matlab model ne source hallucinate kiya."""
    used = []
    invalid = []
    for number in extract_citation_numbers(answer):
        if number in sources:
            used.append(sources[number])
        else:
            invalid.append(number)
    return used, invalid