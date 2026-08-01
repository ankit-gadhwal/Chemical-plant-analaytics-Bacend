from uuid import UUID
from typing import Literal
from pydantic import BaseModel
from enum import Enum

class RAGRequest(BaseModel):
    session_uid: UUID | None = None
    dataset_uid: UUID | None = None
    question: str


class SourceResponse(BaseModel):
    document_uid: UUID
    document_name: str
    page: int | None
    chunk_index: int


class RAGResponse(BaseModel):
    session_uid: UUID | None
    answer: str
    sources: list[SourceResponse]

class DocumentSource(str, Enum):
    USER = "user"
    SYSTEM = "system"

class DocumentMetadata(BaseModel):
    owner_uid: str
    dataset_uid: str
    document_uid: str
    document_name: str
    document_source: DocumentSource
    page: int | None = None

    chunk_index: int