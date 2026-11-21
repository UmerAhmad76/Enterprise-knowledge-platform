"""Checks the OpenSearch mapping: strict mode on, ACL fields are keyword, vector size is correct."""
from core.search_index.mappings.chunks_v1 import chunks_index_body


def test_mapping_is_strict_and_acl_fields_are_keyword():
    body = chunks_index_body(1024)
    props = body["mappings"]["properties"]

    assert body["mappings"]["dynamic"] == "strict"
    assert props["tenant_id"]["type"] == "keyword"
    assert props["allowed_groups"]["type"] == "keyword"
    assert props["allowed_users"]["type"] == "keyword"


def test_vector_dimension_matches_requested_size():
    body = chunks_index_body(768)
    assert body["mappings"]["properties"]["embedding"]["dimension"] == 768
    assert body["settings"]["index"]["knn"] is True