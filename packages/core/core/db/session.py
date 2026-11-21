"""Creates the SQLAlchemy engine and session factory used across the platform."""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str) -> Engine:
    """Builds an engine with connection health checks so dead connections are recycled."""
    return create_engine(database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Returns a factory that produces sessions bound to the given engine."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def check_connection(engine: Engine) -> bool:
    """Runs a trivial query to confirm the database is reachable."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar() == 1