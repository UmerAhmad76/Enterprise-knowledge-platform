"""OpenSearch index mapping for chunks: text for BM25, vectors for kNN, ACL fields for pre-filter."""


def chunks_index_body(dimension: int) -> dict:
    """Index settings aur mappings. dimension embedding model ke output size ke barabar honi chahiye."""
    return {
        "settings": {
            "index": {
                "knn": True,  # kNN plugin on karo
                "number_of_shards": 1,
                "number_of_replicas": 0,  # production mein 1 ya zyada
            },
            "analysis": {
                "analyzer": {"ekp_text": {"type": "standard"}},
            },
        },
        "mappings": {
            # strict: jo field mapping mein nahi, woh reject hoga (galat data index nahi hota)
            "dynamic": "strict",
            "properties": {
                "chunk_id": {"type": "keyword"},
                "tenant_id": {"type": "keyword"},  # mandatory filter
                "document_id": {"type": "keyword"},
                "source_id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "ekp_text"},
                "content": {"type": "text", "analyzer": "ekp_text"},  # BM25 ke liye
                # ACL fields: pre-retrieval filter ke liye keyword hona zaroori hai
                "allowed_groups": {"type": "keyword"},
                "allowed_users": {"type": "keyword"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dimension,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene",
                        "parameters": {"m": 16, "ef_construction": 128},
                    },
                },
            },
        },
    }