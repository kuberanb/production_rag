
from fastapi import APIRouter, File, UploadFile, status

from services.ingestion.app.schemas.document import (
    DocumentUploadResponse,
)

from services.ingestion.app.services.document_service import (
    upload_document,
)

from uuid import UUID

from services.ingestion.app.schemas.document import DocumentStatusResponse
from services.ingestion.app.services.document_service import get_document_status


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_endpoint(
    file: UploadFile = File(...),
):
    document = await upload_document(file)

    return dict(document)


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
)
async def get_document_status_endpoint(
    document_id: UUID,
):
    return await get_document_status(document_id)
