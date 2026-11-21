"""Celery task: ek source ka sync chalata hai. Logic core mein hai, ye file sirf wiring karti hai."""
import os
import uuid

from celery.utils.log import get_task_logger
from sqlalchemy.exc import OperationalError

from core.db.session import make_engine, make_session_factory
from core.ingestion.service import run_source_sync
from worker.celery_app import celery_app

log = get_task_logger(__name__)
_session_factory = None


def _get_session_factory():
    """Engine ek hi baar banta hai, pehli zaroorat par (lazy)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = make_session_factory(make_engine(os.environ["DATABASE_URL"]))
    return _session_factory


@celery_app.task(
    name="ingestion.sync_source",
    autoretry_for=(OperationalError,),  # DB ka temporary issue: retry karo
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def sync_source_task(tenant_id: str, source_id: str) -> dict:
    """IDs string mein aate hen kyunke Celery JSON serialise karta hai. Result dict Redis mein jata hai."""
    with _get_session_factory()() as session:
        report = run_source_sync(session, uuid.UUID(tenant_id), uuid.UUID(source_id))
    log.info(
        "sync done source=%s new=%d changed=%d deleted=%d failed=%d",
        source_id, report.new, report.changed, report.deleted, len(report.failed),
    )
    return {
        "new": report.new,
        "changed": report.changed,
        "unchanged": report.unchanged,
        "deleted": report.deleted,
        "failed": report.failed,
    }