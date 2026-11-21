"""Alembic environment: connects our models' metadata and DATABASE_URL to the migration runner."""
import os
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from core.db.models import Base

# Repo root ka .env load karo (migrations -> db -> core -> core -> packages -> root)
load_dotenv(Path(__file__).resolve().parents[5] / ".env")

config = context.config
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

# % characters config parser mein special hote hain, isliye escape karte hen
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

# Autogenerate yahin se diff nikalta hai: models vs database
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """SQL script generate karta hai bina DB se connect kiye (review ke liye useful)."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Live database se connect karke migrations apply karta hai."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # migrations ke liye pooling ki zaroorat nahi
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()