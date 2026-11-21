"""Builds the OpenSearch clauses that enforce tenant and ACL. Ranking happens only inside this filter."""
from typing import Any

from core.acl.principals import Principals


def build_acl_filter(principals: Principals) -> dict[str, Any]:
    """Tenant lazmi match ho, aur user ya uke kisi group ki permission ho. Dono sath lazmi hain."""
    # should + minimum_should_match=1: user direct allowed ho ya kisi group ke zariye
    should: list[dict[str, Any]] = [{"term": {"allowed_users": str(principals.user_id)}}]
    if principals.group_ids:
        # sorted: same user ka query string har bar same rahe (caching aur debugging ke liye)
        should.append({"terms": {"allowed_groups": sorted(str(g) for g in principals.group_ids)}})

    return {
        "bool": {
            "filter": [{"term": {"tenant_id": str(principals.tenant_id)}}],
            "should": should,
            "minimum_should_match": 1,
        }
    }


def with_acl(query: dict[str, Any], principals: Principals) -> dict[str, Any]:
    """User ki query ko ACL filter ke saath wrap karta hai. Filter query se pehle nahi, saath chalta hai."""
    return {"bool": {"must": [query], "filter": [build_acl_filter(principals)]}}