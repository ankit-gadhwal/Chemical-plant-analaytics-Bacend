import uuid
from datetime import datetime

from pydantic import BaseModel,ConfigDict


class DocumentCreate(BaseModel):
    dataset_uid: uuid.UUID


class DocumentResponse(BaseModel):
    uid: uuid.UUID
    dataset_uid: uuid.UUID
    owner_uid: uuid.UUID

    original_filename: str
    stored_filename: str
    file_path: str

    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]