"""Schema tests on in-memory SQLite: tables exist and constraints reject bad data."""
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.db.models import Base, Document, DocumentACL, Source, Tenant


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    # SQLite foreign keys by default off hoti hain, is liye on karte hen (Postgres mein ye default on hai)
    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)
    engine.dispose()


def make_tenant(session: Session) -> Tenant:
    tenant = Tenant(slug="acme", name="Acme Corp")
    session.add(tenant)
    session.flush()
    return tenant


def make_source(session: Session, tenant: Tenant) -> Source:
    source = Source(tenant_id=tenant.id, kind="confluence", name="Eng wiki", config={})
    session.add(source)
    session.flush()
    return source


def test_all_expected_tables_are_registered():
    expected = {
        "tenants", "users", "groups", "user_groups", "sources", "documents",
        "document_versions", "document_acl", "embedding_versions", "chunks",
        "chat_queries", "feedback",
    }
    assert expected.issubset(Base.metadata.tables.keys())


def test_external_id_is_unique_per_source(session):
    tenant = make_tenant(session)
    source = make_source(session, tenant)

    session.add(Document(tenant_id=tenant.id, source_id=source.id,
                         external_id="DOC-1", title="A", content_hash="h1"))
    session.flush()

    session.add(Document(tenant_id=tenant.id, source_id=source.id,
                         external_id="DOC-1", title="B", content_hash="h2"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_acl_principal_type_is_restricted(session):
    tenant = make_tenant(session)
    source = make_source(session, tenant)
    doc = Document(tenant_id=tenant.id, source_id=source.id,
                   external_id="DOC-2", title="C", content_hash="h3")
    session.add(doc)
    session.flush()

    # 'team' allowed nahi, sirf 'user' ya 'group'
    session.add(DocumentACL(tenant_id=tenant.id, document_id=doc.id,
                            principal_type="team", principal_id=uuid.uuid4()))
    with pytest.raises(IntegrityError):
        session.flush()