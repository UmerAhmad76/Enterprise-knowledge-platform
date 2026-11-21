"""Test helpers: OpenSearch ACL filter ka chhota simulator aur Bearer header banane ka function. Sirf tests ke liye."""
import uuid

from app.auth import create_access_token


def matches(doc: dict, clause: dict) -> bool:
    """Bool, term aur terms clauses ko document par chalata hai, jaise OpenSearch filter karta hai."""
    if "bool" in clause:
        b = clause["bool"]
        ok = all(matches(doc, c) for c in b.get("filter", []) + b.get("must", []))
        if "should" in b:
            hits = sum(matches(doc, c) for c in b["should"])
            ok = ok and hits >= b.get("minimum_should_match", 1)
        return ok
    if "term" in clause:
        (field, value), = clause["term"].items()
        current = doc.get(field)
        return value in current if isinstance(current, list) else current == value
    if "terms" in clause:
        (field, values), = clause["terms"].items()
        return any(v in (doc.get(field) or []) for v in values)
    raise AssertionError(f"unsupported clause: {clause}")


def make_search(index: list[dict]):
    """Fake OpenSearch: query ka ACL filter nikalta hai, aur sirf visible documents wapas deta hai."""

    def search(body: dict) -> list[dict]:
        query = body["query"]
        acl_filter = query["knn"]["embedding"]["filter"] if "knn" in query else query["bool"]["filter"][0]
        return [
            {"_source": {k: doc[k] for k in ("chunk_id", "document_id", "title", "content")}}
            for doc in index
            if matches(doc, acl_filter)
        ]

    return search


def bearer(user_id: uuid.UUID, tenant_id: uuid.UUID) -> dict:
    """Asli signing key se token banata hai, taake auth ka pura path chale."""
    return {"Authorization": f"Bearer {create_access_token(user_id, tenant_id)}"}