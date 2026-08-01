from langchain_google_genai import ChatGoogleGenerativeAI
from src.chatbot.prompts import SQL_GENERATION_PROMPT,ANSWER_GENERATION_PROMPT
from src.config import Config
from src.chatbot.utils import clean_sql,validate_sql
from src.chatbot.sql_executor import SQLExecutor
from src.chatbot.schemas import ChatRequest,ChatResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
from src.datasets.service import DatasetService
from src.error import ( DatasetNotFound,
    AIResponseGenerationFailed,AIServiceUnavailable,
    InvalidQuestion,InvalidSQLGenerated,SQLGenerationFailed,ChatSessionNotFound)
from google.api_core.exceptions import GoogleAPIError
import uuid
from .utils import clean_text
from src.db.models import Dataset,User,ChatSession,ChatMessage,MessageRole,ChatType
from .logger import ChatLogger
from .metrics import Timer
from .schemas import ChatContext
from src.auth.authorization import require_dataset_access
from .repository import ChatRepository
from sqlmodel import select
from langchain_groq import ChatGroq
from groq import (
    APIError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
)

class ChatService:

    def __init__(self):
        self.llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=Config.GROQ_API_KEY,)
        self.repository = ChatRepository()
        self.sql_executor = SQLExecutor()
        self.dataset_service = DatasetService()

#     async def validate_dataset(self,dataset_uid:uuid.UUID,session:AsyncSession)-> Dataset:
#          dataset = await self.dataset_service.get_dataset(dataset_uid,session)
#          if dataset is None:
#               raise DatasetNotFound(f"Dataset '{dataset_uid}' does not exist.")
#          return dataset
    
    async def ask_question(self,request:ChatRequest,current_user:User,session:AsyncSession) -> ChatResponse:

        
        timer = Timer()

        context = ChatContext(request_id=str(uuid.uuid4()),dataset_uid=request.dataset_uid)

        ChatLogger.question(context.request_id,context.dataset_uid,request.question)

        await require_dataset_access(dataset_uid= request.dataset_uid,current_user=current_user,session=session)

        ChatLogger.dataset_validated(context.request_id,context.dataset_uid)

        chat_session = await self.get_or_create_session(session=session,
                                                        owner_uid=current_user.uid,dataset_uid=request.dataset_uid,chat_type=ChatType.SQL,session_uid = request.session_uid)

        chat_history = await self.build_chat_history(session=session,session_uid=chat_session.uid,conversation_limit=5,)

        sql = await self.generate_sql(context=context,question=request.question,chat_history=chat_history,dataset_uid=request.dataset_uid)
        print("generate_sql called")
        
        rows = await self.sql_executor.execute(sql = sql,session=session,context=context)

        answer = await self.generate_answer(context=context,question=request.question,rows=rows)

        await self.save_user_message(session=session,session_uid=chat_session.uid,
                                     message=request.question)
        
        await self.save_assistant_message(session=session,session_uid=chat_session.uid,message=answer)

        ChatLogger.requested_completed(context.request_id,timer.elapsed())

        return ChatResponse(
            session_uid = chat_session.uid,
            question=request.question,answer = answer)
    
    async def generate_sql(self,context: ChatContext,question:str,chat_history: str,dataset_uid:uuid.UUID):

        timer = Timer()

        if not question.strip():
             raise InvalidQuestion()
        
        prompt = SQL_GENERATION_PROMPT.format(
            chat_history=chat_history,
            question=question,
            dataset_uid=dataset_uid
        )

        try:
             response = await self.llm.ainvoke(prompt)

        except AuthenticationError as exc:
             print(exc)
             raise AIServiceUnavailable("Invalid groq API key") from exc

        except RateLimitError as exc:
            print(exc)
            raise AIServiceUnavailable("Groq rate limit exceeded.") from exc

        except APIConnectionError as exc:
            print(exc)
            raise AIServiceUnavailable("Could not connect to Groq.") from exc

        except APIError as exc:
            print(exc)
            raise AIServiceUnavailable() from exc
        except Exception as exc:
             print(type(exc))
             print(exc)
             raise SQLGenerationFailed() from exc
        
        content = response.content
        sql = clean_sql(content)

        print("=" * 80)
        print(sql)
        print("=" * 80)


        try:
             
             validate_sql(sql)

             ChatLogger.generated_sql(context.request_id,sql,timer.elapsed())
        except Exception as exc:
             raise InvalidSQLGenerated(str(exc),) from exc

        return sql
    
    async def generate_answer(self,context:ChatContext,question: str,rows):

        timer = Timer()

        if not rows:
            return "No matching records were found."
        row_json = json.dumps(rows,indent=2,default=str)
        prompt = ANSWER_GENERATION_PROMPT.format(
            question=question,rows=row_json,
        )
        try:
             response = await self.llm.ainvoke(prompt)

             ChatLogger.answer_generated(context.request_id,timer.elapsed())
        except GoogleAPIError as exc:
             raise AIServiceUnavailable() from exc
        except Exception as exc:
             raise AIResponseGenerationFailed() from exc
        content = response.content
        return clean_text(content)

    async def create_chat_session(self,session:AsyncSession,owner_uid:uuid.UUID,
                                  dataset_uid:uuid.UUID,chat_type: ChatType,title: str | None = None) -> ChatSession:
         chat_session = ChatSession(
            owner_uid=owner_uid,
            dataset_uid=dataset_uid,
            title=title,
            chat_type=chat_type,)
         return await self.repository.create_session(session=session,chat_session=chat_session)

    async def get_chat_session(
        self,session: AsyncSession,session_uid: uuid.UUID) -> ChatSession | None:
        return await self.repository.get_session(session=session,session_uid=session_uid,)
    
    async def get_or_create_session(
        self,session: AsyncSession,owner_uid: uuid.UUID,
        dataset_uid: uuid.UUID ,chat_type:ChatType,session_uid: uuid.UUID | None) -> ChatSession:

        if session_uid:

            chat_session = await self.repository.get_user_session(
                session=session,
                session_uid=session_uid,
                owner_uid=owner_uid,
            )

            if chat_session is None:
                raise ChatSessionNotFound()

            if chat_session.chat_type != chat_type:
                raise ChatSessionNotFound()
            
            return chat_session

        return await self.create_chat_session(
            session=session,
            owner_uid=owner_uid,
            dataset_uid=dataset_uid,
            chat_type=chat_type
        )

    async def save_user_message(
        self,session: AsyncSession,session_uid: uuid.UUID,message: str) -> ChatMessage:

        chat_message = ChatMessage(session_uid=session_uid,
            role=MessageRole.User,message=message)
        return await self.repository.save_message(
            session=session,
            chat_message=chat_message)

    async def save_assistant_message(self,session: AsyncSession,
        session_uid: uuid.UUID,message: str) -> ChatMessage:
        chat_message = ChatMessage(
            session_uid=session_uid,
            role=MessageRole.ASSISTANT,
            message=message)

        return await self.repository.save_message(session=session,chat_message=chat_message)

    async def get_chat_history(self,session: AsyncSession,
                               session_uid: uuid.UUID,conversation_limit: int = 5) -> list[ChatMessage]:

        return await self.repository.get_recent_messages(session=session,
                                                         session_uid=session_uid,conversation_limit=conversation_limit)

    async def build_chat_history(self,session: AsyncSession,
        session_uid: uuid.UUID,conversation_limit: int = 5) -> str:

        messages = await self.get_chat_history(
            session=session,session_uid=session_uid,conversation_limit=conversation_limit)

        history = []

        for message in messages:
            history.append(f"{message.role.value}:\n{message.message}")

        return "\n\n".join(history)

    async def get_session_messages(
    self,
    session: AsyncSession,
    session_uid: uuid.UUID,) -> list[ChatMessage]:
        statement = (
        select(ChatMessage)
        .where(ChatMessage.session_uid == session_uid)
        .order_by(ChatMessage.created_at.asc()))

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_chat_sessions(
            self,session: AsyncSession,
            owner_uid: uuid.UUID,) -> list[ChatSession]:

            return await self.repository.list_sessions(session=session,
                                                       owner_uid=owner_uid,)


    async def get_chat_session_history(
            self,session: AsyncSession,
    session_uid: uuid.UUID,owner_uid: uuid.UUID,):
        chat_session = await self.repository.get_user_session(
        session=session,
        session_uid=session_uid,
        owner_uid=owner_uid,
        )

        if chat_session is None:
            raise ChatSessionNotFound()

        messages = await self.get_session_messages(session=session,session_uid=session_uid,)

        return {"session": chat_session,
                "messages": messages,}

    async def delete_chat_session(self,session: AsyncSession,
    session_uid: uuid.UUID,owner_uid: uuid.UUID,):
        chat_session = await self.repository.get_user_session(
        session=session,
        session_uid=session_uid,
        owner_uid=owner_uid)

        if chat_session is None:
            raise ChatSessionNotFound()

        await self.repository.delete_session(
            session=session,chat_session=chat_session)

        return True