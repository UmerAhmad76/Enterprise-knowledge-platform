"""Retrieval metrics: recall@k, MRR, nDCG, aur ACL leaks. Sab document-level hain (title par), chunk-level nahi."""
import math
from collections.abc import Iterable


def dedupe(titles: Iterable[str]) -> list[str]:
    """Same document ke multiple chunks ko ek hi entry banata hai, order maintain karte hue."""
    seen: set[str] = set()
    out: list[str] = []
    for title in titles:
        if title not in seen:
            seen.add(title)
            out.append(title)
    return out


def recall_at_k(retrieved: Iterable[str], expected: Iterable[str], k: int) -> float:
    """Top-k mein kitne expected documents mile, un ka fraction (0 se 1)."""
    expected_set = set(expected)
    top = set(dedupe(retrieved)[:k])
    return len(top & expected_set) / len(expected_set)


def mrr(retrieved: Iterable[str], expected: Iterable[str]) -> float:
    """Pehle relevant document ka reciprocal rank. Jitna upar, utna behtar."""
    expected_set = set(expected)
    for rank, title in enumerate(dedupe(retrieved), start=1):
        if title in expected_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: Iterable[str], expected: Iterable[str], k: int) -> float:
    """Binary relevance nDCG: relevant documents upar hon to score 1 ke qareeb."""
    expected_set = set(expected)
    ranked = dedupe(retrieved)[:k]
    dcg = sum(1.0 / math.log2(i + 1) for i, t in enumerate(ranked, start=1) if t in expected_set)
    ideal_hits = min(len(expected_set), k)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / ideal


def leaked_titles(retrieved: Iterable[str], forbidden: Iterable[str], k: int) -> list[str]:
    """Top-k mein woh documents jo is user ke liye forbidden the. Ye list khaali honi chahiye."""
    forbidden_set = set(forbidden)
    return sorted(set(dedupe(retrieved)[:k]) & forbidden_set)