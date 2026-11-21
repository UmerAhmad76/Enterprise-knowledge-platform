"""OpenSearch query builders. Har query lazmi ACL filter ke saath wrap hoti hai, koi raw query nahi bhejte."""
from typing import Any

from core.acl.filters import with_acl
from core.acl.principals import Principals


def bm25_query(text: str, principals: Principals, size: int = 50) -> dict[str, Any]:
    """Keyword search: title aur content par multi-match, ACL filter ke andar."""
    body = {
        "size": size,
        "_source": ["chunk_id", "document_id", "title", "content"],
        "query": {
            "multi_match": {
                "query": text,
                "fields": ["title^2", "content"],  # title ka weight zyada, kyunke title aksar zyada relevant hota hai
            }
        },
    }
    body["query"] = with_acl(body["query"], principals)
    return body


def knn_query(vector: list[float], principals: Principals, size: int = 50) -> dict[str, Any]:
    """Vector search: kNN clause ke andar hi ACL filter lagta hai, taake pre-filtering ho."""
    body = {
        "size": size,
        "_source": ["chunk_id", "document_id", "title", "content"],
        "query": {
            "knn": {
                "embedding": {
                    "vector": vector,
                    "k": size,
                    "filter": build_acl_filter_clause(principals),
                }
            }
        },
    }
    return body


def build_acl_filter_clause(principals: Principals) -> dict[str, Any]:
    """kNN ka filter parameter bhi wahi ACL shape use karta hai jo BM25 mein hai, ek hi source of truth."""
    from core.acl.filters import build_acl_filter

    return build_acl_filter(principals)