"""Dev helper: tenant ke liye local_fs source banata hai. --group se ACL set hoti hai, warna koi user documents nahi dekh sakta."""
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

from core.db.models import Group, Source, Tenant
from core.db.session import make_engine, make_session_factory


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a local folder as a document source.")
    parser.add_argument("tenant_slug")
    parser.add_argument("root")
    parser.add_argument("--group", action="append", default=[], help="allowed group name (repeatable)")
    args = parser.parse_args()

    load_dotenv()
    session_factory = make_session_factory(make_engine(os.environ["DATABASE_URL"]))
    with session_factory() as db:
        tenant = db.execute(select(Tenant).where(Tenant.slug == args.tenant_slug)).scalar_one()
        group_ids = []
        for name in args.group:
            group = db.execute(
                select(Group).where(Group.tenant_id == tenant.id, Group.name == name)
            ).scalar_one()
            group_ids.append(str(group.id))

        source = Source(
            tenant_id=tenant.id,
            kind="local_fs",
            name=f"local:{Path(args.root).name}",
            config={"root": str(Path(args.root).resolve()), "allowed_group_ids": group_ids},
        )
        db.add(source)
        db.commit()

        print(f"source_id={source.id}")
        print(f"allowed groups: {args.group or 'none (nobody can see these documents)'}")


if __name__ == "__main__":
    main()