"""ACL tests: identity resolution, tenant isolation, inactive users, and the generated filter shape."""
import pytest

from core.acl.filters import build_acl_filter, with_acl
from core.acl.principals import Principals, resolve_principals
from core.common.errors import AccessDeniedError, NotFoundError
from core.db.models import Group, Tenant, User


@pytest.fixture
def world(db_session):
    """Do tenants: acme (alice, bob) aur globex (eve). Alice sirf eng group mein hai."""
    acme = Tenant(slug="acme", name="Acme")
    globex = Tenant(slug="globex", name="Globex")
    db_session.add_all([acme, globex])
    db_session.flush()

    eng = Group(tenant_id=acme.id, name="eng")
    hr = Group(tenant_id=acme.id, name="hr")
    alice = User(tenant_id=acme.id, email="alice@acme.test", display_name="Alice")
    bob = User(tenant_id=acme.id, email="bob@acme.test", display_name="Bob", is_active=False)
    eve = User(tenant_id=globex.id, email="eve@globex.test", display_name="Eve")
    alice.groups.append(eng)
    db_session.add_all([eng, hr, alice, bob, eve])
    db_session.flush()
    return {"acme": acme, "globex": globex, "eng": eng, "alice": alice, "bob": bob, "eve": eve}


def test_resolves_user_and_only_own_groups(db_session, world):
    p = resolve_principals(db_session, world["acme"].id, world["alice"].id)
    assert p.group_ids == frozenset({world["eng"].id})


def test_user_from_another_tenant_is_not_found(db_session, world):
    # Eve globex ki hai, lekin token acme ka bata raha hai: ye 'not found' hona chahiye
    with pytest.raises(NotFoundError):
        resolve_principals(db_session, world["acme"].id, world["eve"].id)


def test_inactive_user_is_denied(db_session, world):
    with pytest.raises(AccessDeniedError):
        resolve_principals(db_session, world["acme"].id, world["bob"].id)


def test_filter_enforces_tenant_user_and_groups(db_session, world):
    p = resolve_principals(db_session, world["acme"].id, world["alice"].id)
    f = build_acl_filter(p)["bool"]

    assert {"term": {"tenant_id": str(world["acme"].id)}} in f["filter"]
    assert {"term": {"allowed_users": str(world["alice"].id)}} in f["should"]
    assert {"terms": {"allowed_groups": [str(world["eng"].id)]}} in f["should"]
    assert f["minimum_should_match"] == 1


def test_user_without_groups_gets_no_group_clause():
    import uuid

    p = Principals(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())
    should = build_acl_filter(p)["bool"]["should"]
    assert len(should) == 1
    assert "allowed_users" in should[0]["term"]


def test_with_acl_wraps_user_query_with_filter(db_session, world):
    p = resolve_principals(db_session, world["acme"].id, world["alice"].id)
    user_query = {"match": {"content": "vacation policy"}}
    wrapped = with_acl(user_query, p)

    assert wrapped["bool"]["must"] == [user_query]
    assert wrapped["bool"]["filter"] == [build_acl_filter(p)]