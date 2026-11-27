
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status, HTTPException

from services.ingestion.app.schemas.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
)

from services.ingestion.app.services.document_service import (
    upload_document,
    get_document_status,
    delete_document,
)

from shared.exceptions import DocumentNotFoundError


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


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_document_endpoint(
    document_id: UUID,
):
    try:
        result = await delete_document(document_id)

        return {
            "message": "Document deleted successfully",
            **result,
        }

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
