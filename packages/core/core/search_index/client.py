"""OpenSearch client factory. URL env se aata hai, TLS sirf https par on hota hai."""
from opensearchpy import OpenSearch


def make_opensearch_client(url: str, timeout: int = 30) -> OpenSearch:
    secure = url.startswith("https")
    return OpenSearch(
        hosts=[url],
        timeout=timeout,
        use_ssl=secure,
        verify_certs=secure,
    )