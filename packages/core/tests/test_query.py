"""Query shape tests: har query mein ACL filter hona lazmi hai. Ye test leak ke khilaf guard hai."""
import uuid

from core.acl.principals import Principals
from core.retrieval.query import bm25_query, knn_query


def make_principals() -> Principals:
    return Principals(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        tenant_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        group_ids=frozenset({uuid.UUID("33333333-3333-3333-3333-333333333333")}),
    )


def test_bm25_query_is_wrapped_with_tenant_and_acl_filter():
    body = bm25_query("leave policy", make_principals())
    filters = body["query"]["bool"]["filter"]
    assert len(filters) == 1
    assert {"term": {"tenant_id": "22222222-2222-2222-2222-222222222222"}} in filters[0]["bool"]["filter"]


def test_knn_filter_is_inside_knn_clause_for_pre_filtering():
    body = knn_query([0.1, 0.2], make_principals())
    knn = body["query"]["knn"]["embedding"]
    assert knn["filter"]["bool"]["minimum_should_match"] == 1
    assert {"term": {"tenant_id": "22222222-2222-2222-2222-222222222222"}} in knn["filter"]["bool"]["filter"]


def test_both_queries_carry_the_same_acl_shape():
    p = make_principals()
    bm25_filter = bm25_query("x", p)["query"]["bool"]["filter"][0]
    knn_filter = knn_query([0.0], p)["query"]["knn"]["embedding"]["filter"]
    assert bm25_filter == knn_filter


def test_size_is_respected():
    assert bm25_query("x", make_principals(), size=7)["size"] == 7
    assert knn_query([0.0], make_principals(), size=7)["query"]["knn"]["embedding"]["k"] == 7