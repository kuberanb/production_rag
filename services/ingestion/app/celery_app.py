
from celery import Celery

from shared.config import settings


celery_app = Celery(
    "ingestion",
    broker=settings.redis_url,
    include=[
        "services.ingestion.app.workers.tasks.document_tasks"
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    task_ignore_result=True,

    task_acks_late=True,
    worker_prefetch_multiplier=1,

    broker_connection_retry_on_startup=True,

    timezone="UTC",
    enable_utc=True,
)
