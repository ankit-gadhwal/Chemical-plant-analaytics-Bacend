from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .rag.schemas import RAGResponse,RAGRequest
from src.chatbot.schemas import (ChatResponse,ChatRequest,ChatSessionResponse,
                                 ChatHistoryResponse,ChatMessageResponse)
from src.chatbot.service import ChatService
from src.db.main import get_session
from src.db.models import User
from src.auth.authorization import get_current_user
from .rag.rag_service import RAGService
from uuid import UUID
from fastapi.exceptions import HTTPException

chat_router = APIRouter()
chat_service = ChatService()
rag_service = RAGService()

@chat_router.post("/sql",response_model=ChatResponse)
async def ask_question(request:ChatRequest,current_user: User = Depends(get_current_user),session:AsyncSession = Depends(get_session)):
    return await chat_service.ask_question(request=request,current_user=current_user,session=session)

@chat_router.post("/rag",response_model=RAGResponse)
async def ask_document_question(request: RAGRequest,session:AsyncSession = Depends(get_session),
                                current_user: User = Depends(get_current_user)):

    return await rag_service.answer(
        question=request.question,
        owner_uid=current_user.uid,
        session=session,
        dataset_uid=request.dataset_uid,session_uid=request.session_uid)

@chat_router.get("/sessions", response_model=list[ChatSessionResponse])
async def get_sessions(
    user: User=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    sessions = await chat_service.get_chat_sessions(
        session=session,
        owner_uid=user.uid,
    )

    return [
        ChatSessionResponse(
            session_uid=s.uid,
            dataset_uid=s.dataset_uid,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]

@chat_router.get("/sessions/{session_uid}",response_model=ChatHistoryResponse)
async def get_chat_history(session_uid:UUID,current_user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)):

    history = await chat_service.get_chat_session_history(session=session,session_uid=session_uid,
                                                          owner_uid = current_user.uid)

    return ChatHistoryResponse(
        session=ChatSessionResponse(
        session_uid=history["session"].uid,
        title=history["session"].title,
        created_at=history["session"].created_at,
        updated_at=history["session"].updated_at,
    ),
        messages = [
            ChatMessageResponse(
                uid= m.uid,
                role=m.role,
                message = m.message,
                created_at=m.created_at,
            )
            for m in history["messages"]
        ]
    )
@chat_router.delete("/sessions/{session_uid}")
async def delete_chat_session(session_uid: UUID,
    user:User=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    deleted = await chat_service.delete_chat_session(session=session,
        session_uid=session_uid,
        owner_uid=user.uid,
    )

    if deleted is None:
        raise HTTPException(404, "Session not found")

    return {
        "message": "Chat session deleted successfully."
    }