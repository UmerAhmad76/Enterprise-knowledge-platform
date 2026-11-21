"""Wires the core DB session into the API: one engine per process, one session per request."""
from collections.abc import Iterator

from core.db.session import make_engine, make_session_factory
from sqlalchemy.orm import Session

from app.config import get_settings

settings = get_settings()
engine = make_engine(settings.database_url)
SessionLocal = make_session_factory(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: opens a session for the request and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()