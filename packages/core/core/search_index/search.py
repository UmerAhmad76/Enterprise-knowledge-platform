"""Adapter: OpenSearch client ko retrieval ke SearchFn contract mein badalta hai."""
from typing import Any

from opensearchpy import OpenSearch

from core.retrieval.pipeline import SearchFn


def make_search(client: OpenSearch, index: str) -> SearchFn:
    """Retrieval pipeline ko ek function deta hai jo body leta hai aur hits return karta hai."""

    def search(body: dict[str, Any]) -> list[dict[str, Any]]:
        response = client.search(index=index, body=body)
        return response["hits"]["hits"]

    return search