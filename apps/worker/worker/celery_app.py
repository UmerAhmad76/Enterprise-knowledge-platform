"""Celery app: broker config aur reliability settings. Ingestion workers isi se start hote hen."""
import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ekp",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker.tasks.sync_source"],
)

celery_app.conf.update(
    task_acks_late=True,              # task complete hone par ack: worker crash ho to task dobara milega
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,     # lamba sync baaki tasks ko block na kare
    timezone="UTC",
    enable_utc=True,
)