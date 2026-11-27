
from pathlib import Path
from uuid import uuid4

from uuid import UUID

from shared.exceptions import DocumentNotFoundError
from services.ingestion.app.workers.tasks.document_tasks import process_document

from services.ingestion.app.repositories.document_repository import (
    create_document,
    get_document_by_id,
    delete_document_by_id,
)

import asyncio
import logging
import aiofiles

from fastapi import UploadFile
from shared.config import settings
from shared.exceptions import InvalidFileError

from services.ingestion.app.repositories.document_repository import create_document

logger = logging.getLogger(__name__)

async def upload_document(file:UploadFile):

    # 1. Validate filename
    if not file.filename:
        raise InvalidFileError("File name is required")

    if Path(file.filename).suffix.lower() != ".pdf":
        raise InvalidFileError("Only Pdf Files are allowed")

    # 2. Check PDF signature
    file_header = await file.read(5)

    if file_header != b"%PDF-":
        raise InvalidFileError("Invalid PDF file")

    # Reset file position
    await file.seek(0)

    # 3. Generate a unique storage filename
    document_id = uuid4()

    stored_filename = f"{document_id}.pdf"
    upload_directory = Path(settings.upload_dir)
    upload_directory.mkdir(parents=True,exist_ok=True)

    file_path = upload_directory / stored_filename

    # 4. Save file with size validation
    file_size = 0

    try:

        async with aiofiles.open(file_path,"wb") as output_file:

            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)

                if file_size > settings.max_upload_size:
                    raise InvalidFileError(
                        "File size exceeds the allowed limit"
                    )

                await output_file.write(chunk)

            if file_size == 0:
              raise InvalidFileError("Uploaded file is empty")

        # 5. Insert document record into PostgreSQL
        document = await create_document(
            filename=Path(file.filename).name,
            file_path=str(file_path),
        )

        process_document.delay(str(document["id"]))

        return document

    except Exception:
        # Remove the saved file if database insertion or upload fails
        if file_path.exists():
            file_path.unlink()

        raise
 

async def get_document_status(document_id:UUID):

    document = await get_document_by_id(document_id)

    if document is None:
        raise DocumentNotFoundError()

    return document


async def delete_document(document_id: UUID):

    # Check whether the document exists.
    document = await get_document_by_id(document_id)

    if document is None:
        raise DocumentNotFoundError()

    # Prevent deletion while ingestion is running.
    if document["status"] == "processing":
        raise ValueError(
            "Cannot delete a document while it is processing"
        )

    # Delete the database record and associated chunks.
    deleted_document = await delete_document_by_id(document_id)

    if deleted_document is None:
        raise ValueError(
            "Document could not be deleted. It may have started processing."
        )

    # Delete the physical PDF file.
    file_path = Path(deleted_document["file_path"])

    file_cleanup_success = True

    try:
        await asyncio.to_thread(
            file_path.unlink,
            missing_ok=True,
        )

    except OSError:
        file_cleanup_success = False

        logger.exception(
            "Failed to delete PDF file: %s",
            file_path,
        )

    return {
        "id": str(deleted_document["id"]),
        "filename": deleted_document["filename"],
        "file_cleanup_success": file_cleanup_success,
    }

