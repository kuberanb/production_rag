
import asyncio

from services.ingestion.app.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="ingestion.process_document",
    max_retries=3,
    default_retry_delay=10,
)
def process_document(self, document_id: str):

    from services.ingestion.app.services.document_processing_service import (
        process_document_async,
    )

    try:
        asyncio.run(
            process_document_async(
                document_id=document_id,
            )
        )

    except Exception as exc:
        raise self.retry(exc=exc)
