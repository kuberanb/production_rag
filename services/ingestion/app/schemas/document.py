

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    created_at: datetime

class DocumentStatusResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime



    model_config = ConfigDict(from_attributes=True)

