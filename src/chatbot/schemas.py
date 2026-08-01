from pydantic import BaseModel
import uuid
from dataclasses import dataclass
from typing import Optional
from src.db.models import MessageRole
from datetime import datetime

class ChatSessionResponse(BaseModel):
    session_uid: uuid.UUID
    dataset_uid: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    role: str
    message: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session_uid: uuid.UUID
    title: str | None
    messages: list[ChatMessageResponse]

class ChatRequest(BaseModel):
    session_uid:Optional[uuid.UUID] = None
    dataset_uid: uuid.UUID
    question:str

class ChatResponse(BaseModel):
    question: str
    answer: str

class ChatSessionCreate(BaseModel):
    dataset_uid: uuid.UUID
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    session_uid: uuid.UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    uid: uuid.UUID
    role: MessageRole
    message: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: list[ChatMessageResponse]


@dataclass
class ChatContext:
     request_id: str
     dataset_uid: uuid.UUID