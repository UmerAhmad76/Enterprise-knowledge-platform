"""ACL leakage matrix: har principal ke liye visible documents exact expected set ke barabar hone chahiye. Ek bhi extra document = leak."""
import uuid

import pytest

from core.acl.filters import build_acl_filter
from core.acl.principals import Principals

ACME, GLOBEX = str(uuid.uuid4()), str(uuid.uuid4())
ACME_ENG, ACME_HR, GLOBEX_ENG = (str(uuid.uuid4()) for _ in range(3))
ALICE, BOB, CAROL, DAN, EVE = (str(uuid.uuid4()) for _ in range(5))

# Documents index mein jis shape mein stored hain, wahi shape
DOCS = [
    {"id": "d1", "tenant_id": ACME, "allowed_groups": [ACME_ENG], "allowed_users": []},
    {"id": "d2", "tenant_id": ACME, "allowed_groups": [ACME_HR], "allowed_users": []},
    {"id": "d3", "tenant_id": ACME, "allowed_groups": [], "allowed_users": [DAN]},
    {"id": "d4", "tenant_id": ACME, "allowed_groups": [ACME_ENG], "allowed_users": [BOB]},
    {"id": "d5", "tenant_id": GLOBEX, "allowed_groups": [GLOBEX_ENG], "allowed_users": []},
]

# (principals, jo documents dikhne chahiye). Ye expected sets haath se likhe gaye hain.
CASES = {
    "alice": (
        Principals(user_id=uuid.UUID(ALICE), tenant_id=uuid.UUID(ACME), group_ids=frozenset({uuid.UUID(ACME_ENG)})),
        {"d1", "d4"},
    ),
    "bob": (
        Principals(user_id=uuid.UUID(BOB), tenant_id=uuid.UUID(ACME), group_ids=frozenset({uuid.UUID(ACME_HR)})),
        {"d2", "d4"},
    ),
    "carol": (
        Principals(
            user_id=uuid.UUID(CAROL),
            tenant_id=uuid.UUID(ACME),
            group_ids=frozenset({uuid.UUID(ACME_ENG), uuid.UUID(ACME_HR)}),
        ),
        {"d1", "d2", "d4"},
    ),
    "dan": (
        Principals(user_id=uuid.UUID(DAN), tenant_id=uuid.UUID(ACME), group_ids=frozenset()),
        {"d3"},
    ),
    "eve": (
        Principals(user_id=uuid.UUID(EVE), tenant_id=uuid.UUID(GLOBEX), group_ids=frozenset({uuid.UUID(GLOBEX_ENG)})),
        {"d5"},
    ),
    # Eve ke paas acme ka group ID hai (galat tenant): kuch bhi nahi dikhna chahiye
    "eve-with-acme-group": (
        Principals(user_id=uuid.UUID(EVE), tenant_id=uuid.UUID(GLOBEX), group_ids=frozenset({uuid.UUID(ACME_ENG)})),
        set(),
    ),
}


def opensearch_matches(doc: dict, clause: dict) -> bool:
    """Chhota evaluator: bool, term, terms samajhta hai, taake filter ka asar bina Docker ke dekha ja sake."""
    if "bool" in clause:
        b = clause["bool"]
        ok = all(opensearch_matches(doc, c) for c in b.get("filter", []) + b.get("must", []))
        if "should" in b:
            hits = sum(opensearch_matches(doc, c) for c in b["should"])
            ok = ok and hits >= b.get("minimum_should_match", 1)
        return ok
    if "term" in clause:
        (field, value), = clause["term"].items()
        current = doc.get(field)
        return (value in current) if isinstance(current, list) else (current == value)
    if "terms" in clause:
        (field, values), = clause["terms"].items()
        current = doc.get(field) or []
        return any(v in current for v in values)
    raise AssertionError(f"unsupported clause: {clause}")


@pytest.mark.parametrize("name", list(CASES))
def test_visible_documents_match_expectation(name):
    principals, expected = CASES[name]
    flt = build_acl_filter(principals)
    visible = {d["id"] for d in DOCS if opensearch_matches(d, flt)}
    assert visible == expected, f"{name} sees {sorted(visible)}, expected {sorted(expected)}"


def test_every_filter_pins_the_tenant():
    for name, (principals, _) in CASES.items():
        required = {"term": {"tenant_id": str(principals.tenant_id)}}
        assert required in build_acl_filter(principals)["bool"]["filter"], name