
import asyncio
import logging
from uuid import UUID

from celery import Task

from services.ingestion.app.celery_app import celery_app

logger = logging.getLogger(__name__)


async def mark_document_failed_async(
    document_id: str,
    error_message: str,
):
    from shared.database import (
        connect_to_database,
        close_database_connection,
    )
    from services.ingestion.app.repositories.document_repository import (
        update_document_status,
    )

    database_connected = False

    try:
        await connect_to_database()
        database_connected = True

        await update_document_status(
            document_id=UUID(document_id),
            status="failed",
            error_message=error_message,
        )

    finally:
        if database_connected:
            await close_database_connection()


@celery_app.task(
    bind=True,
    name="ingestion.process_document",
    max_retries=3,
    default_retry_delay=10,
)
def process_document(self: Task, document_id: str):

    from services.ingestion.app.services.document_processing_service import (
        process_document_async,
    )

    try:
        return asyncio.run(
            process_document_async(document_id=document_id)
        )

    except Exception as exc:

        # All retry attempts have been exhausted.
        if self.request.retries >= self.max_retries:

            logger.exception(
                "Document processing failed permanently: %s",
                document_id,
            )

            try:
                asyncio.run(
                    mark_document_failed_async(
                        document_id=document_id,
                        error_message=str(exc),
                    )
                )
            except Exception:
                logger.exception(
                    "Could not update document status to failed: %s",
                    document_id,
                )

            raise

        # Retry the task if attempts remain.
        logger.warning(
            "Document processing failed. Retrying document %s. "
            "Retry %s of %s",
            document_id,
            self.request.retries + 1,
            self.max_retries,
        )

        raise self.retry(exc=exc)
