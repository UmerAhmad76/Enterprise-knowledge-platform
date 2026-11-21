"""Reciprocal Rank Fusion: BM25 aur vector results ko rank se merge karta hai, score se nahi."""
from collections.abc import Sequence


def rrf_fuse(rankings: Sequence[Sequence[str]], k: int = 60, top_n: int = 50) -> list[tuple[str, float]]:
    """Har list mein item ka rank (1 se shuru) le kar 1/(k + rank) jodta hai. Zyada lists mein aana score badhata hai."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    # Score ghatte order mein, barabar score par ID se stable order
    fused = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    return fused[:top_n]