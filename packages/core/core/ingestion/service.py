"""Application entry point: tenant ke source ko load karo, sync chalao, aur result save karo."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.common.errors import NotFoundError
from core.db.models import Document, Source
from core.db.models.base import utcnow
from core.ingestion.factory import build_connector
from core.ingestion.pipeline import SyncReport, sync_source
from core.ingestion.store_sql import SqlDocumentStore


def run_source_sync(session: Session, tenant_id: uuid.UUID, source_id: uuid.UUID) -> SyncReport:
    source = session.execute(
        select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if source is None:
        # Doosre tenant ka source bhi yahi error dega, existence ka pata nahi chalna chahiye
        raise NotFoundError("source not found")

    connector = build_connector(source.kind, source.config)
    store = SqlDocumentStore(session, tenant_id, source.id)
    try:
        report = sync_source(connector, store)
        source.last_synced_at = utcnow()
        _stamp_acl_synced(session, tenant_id, source.id, report.upserted_ids)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return report


def _stamp_acl_synced(
    session: Session, tenant_id: uuid.UUID, source_id: uuid.UUID, touched_external_ids: list[str]
) -> None:
    """Har document jiski ACL is sync mein check ya update hui, uska acl_synced_at update karta hai (drift monitor ke liye)."""
    if not touched_external_ids:
        return
    documents = session.execute(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.source_id == source_id,
            Document.external_id.in_(touched_external_ids),
        )
    ).scalars().all()
    now = utcnow()
    for doc in documents:
        doc.acl_synced_at = now