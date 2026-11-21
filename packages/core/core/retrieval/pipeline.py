"""Retrieval orchestration: BM25 aur kNN dono chalao, RRF se merge karo, optional reranker lagao."""
from collections.abc import Callable
from typing import Any

from core.acl.principals import Principals
from core.embeddings.base import Embedder
from core.retrieval.fusion import rrf_fuse
from core.retrieval.query import bm25_query, knn_query
from core.retrieval.reranker import Reranker
from core.retrieval.types import RetrievedChunk

# Search backend ek function hai: body lo, hits ki list do. OpenSearch isi se wire hoga.
SearchFn = Callable[[dict[str, Any]], list[dict[str, Any]]]


def retrieve(
    question: str,
    principals: Principals,
    embedder: Embedder,
    search: SearchFn,
    top_k: int = 8,
    candidates: int = 50,
    reranker: Reranker | None = None,
) -> list[RetrievedChunk]:
    """Dono searches ek hi principals ke saath chalti hain. Pehla hit har chunk ka source maana jata hai."""
    bm25_hits = search(bm25_query(question, principals, size=candidates))
    vector = embedder.embed_query(question)
    knn_hits = search(knn_query(vector, principals, size=candidates))

    source_of: dict[str, dict[str, Any]] = {}
    for hit in bm25_hits + knn_hits:
        src = hit["_source"]
        source_of.setdefault(src["chunk_id"], src)

    fused = rrf_fuse(
        [
            [h["_source"]["chunk_id"] for h in bm25_hits],
            [h["_source"]["chunk_id"] for h in knn_hits],
        ],
        top_n=candidates,
    )
    ranked = [
        RetrievedChunk(
            chunk_id=cid,
            document_id=source_of[cid]["document_id"],
            score=score,
            title=source_of[cid].get("title", ""),
            text=source_of[cid].get("content", ""),
        )
        for cid, score in fused
    ]

    if reranker is None:
        return ranked[:top_k]
    return reranker.rerank(question, ranked, top_k)