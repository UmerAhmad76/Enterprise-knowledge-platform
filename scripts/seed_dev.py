"""Dev-only seed: one tenant, two groups, two users with memberships. Safe to run more than once."""
import os

from dotenv import load_dotenv
from sqlalchemy import select

from core.db.models import Group, Tenant, User
from core.db.session import make_engine, make_session_factory


def get_or_create(db, model, defaults: dict | None = None, **lookup):
    """Row mil jaye to wahi return karo, warna banao. Isi se script dobara chalane par duplicate nahi banta."""
    obj = db.execute(select(model).filter_by(**lookup)).scalar_one_or_none()
    if obj is None:
        obj = model(**lookup, **(defaults or {}))
        db.add(obj)
        db.flush()
    return obj


def main() -> None:
    load_dotenv()  # repo root ki .env se DATABASE_URL uthata hai
    session_factory = make_session_factory(make_engine(os.environ["DATABASE_URL"]))

    with session_factory() as db:
        tenant = get_or_create(db, Tenant, slug="acme", defaults={"name": "Acme Corp"})
        eng = get_or_create(db, Group, tenant_id=tenant.id, name="eng")
        hr = get_or_create(db, Group, tenant_id=tenant.id, name="hr-managers")
        alice = get_or_create(db, User, tenant_id=tenant.id, email="alice@acme.test",
                              defaults={"display_name": "Alice"})
        bob = get_or_create(db, User, tenant_id=tenant.id, email="bob@acme.test",
                            defaults={"display_name": "Bob"})

        if eng not in alice.groups:
            alice.groups.append(eng)
        if hr not in bob.groups:
            bob.groups.append(hr)
        db.commit()

        print(f"tenant: acme ({tenant.id})")
        print(f"alice@acme.test  groups: eng ({eng.id})")
        print(f"bob@acme.test    groups: hr-managers ({hr.id})")


if __name__ == "__main__":
    main()