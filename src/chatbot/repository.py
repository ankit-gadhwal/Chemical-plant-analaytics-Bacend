from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import ChatSession, ChatMessage, MessageRole,ChatType

class ChatRepository:
    async def create_session(self,session: AsyncSession,chat_session: ChatSession,) -> ChatSession:
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
        return chat_session

    async def save_message(
        self,session: AsyncSession,chat_message: ChatMessage,) -> ChatMessage:

        session.add(chat_message)
        await session.commit()
        await session.refresh(chat_message)
        return chat_message

    async def get_session(self,
        session: AsyncSession,session_uid: UUID) -> ChatSession | None:
        statement = select(ChatSession).where(
            ChatSession.uid == session_uid)

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def list_sessions(
        self,session: AsyncSession,owner_uid: UUID,chat_type: ChatType | None = None,) -> list[ChatSession]:
        statement = (
            select(ChatSession)
            .where(ChatSession.owner_uid == owner_uid)
        )
        if chat_type is not None:
            statement = statement.where(
                ChatSession.chat_type == chat_type
            )

        statement = statement.order_by(
            ChatSession.updated_at.desc()
        )
        result = await session.execute(statement)
        return result.scalars().all()

    async def get_recent_messages(
        self,session: AsyncSession,session_uid: UUID,
        conversation_limit: int = 5) -> list[ChatMessage]:

        message_limit = conversation_limit * 2

        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_uid == session_uid)
            .order_by(ChatMessage.created_at.desc())
            .limit(message_limit))
        
        result = await session.execute(statement)
        messages = result.scalars().all()
        return list(reversed(messages))

    async def update_session(
        self,session: AsyncSession,chat_session: ChatSession) -> ChatSession:
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
        return chat_session

    async def delete_session(
        self,
        session: AsyncSession,
        chat_session: ChatSession,
    ) -> None:
        await session.delete(chat_session)
        await session.commit()

    async def get_user_session(self,session: AsyncSession,session_uid: UUID,
                               owner_uid: UUID,) -> ChatSession | None:
           statement = (select(ChatSession).where(ChatSession.uid == session_uid,
                                                  ChatSession.owner_uid == owner_uid))

           result = await session.execute(statement)
           return result.scalar_one_or_none()