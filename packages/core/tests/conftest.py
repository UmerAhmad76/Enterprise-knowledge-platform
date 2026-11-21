"""Shared fixture: fresh in-memory database with the full schema, foreign keys enforced."""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from core.db.models import Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, _):
        # SQLite mein foreign keys default off hoti hain, Postgres ki behaviour ke liye on karte hen
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()