from uuid import UUID
from langchain_core.documents import Document
from .embeddings import embedding_service
from .vector_store import VectorStore
from .retriever import Retriever
from .schemas import (RAGResponse,SourceResponse)
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import Config
from langchain_groq import ChatGroq
import re
from src.chatbot.service import ChatService
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import ChatType

class RAGService:

    def __init__(self):

        self.embedding_service = embedding_service
        self.vector_store = VectorStore()
        self.retriever = Retriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,)

        self.llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=Config.GROQ_API_KEY,)
        self.chat_service = ChatService()

    def build_context(self,documents: list[Document]) -> str:

        context = []

        for i,doc in enumerate(documents,start=1):
            context.append(
                f"""
Source {i}

Document: {doc.metadata.get("document_name")}
Page: {doc.metadata.get("page")}

{doc.page_content}
"""
        )

        return "\n\n".join(context)            


    def build_prompt(self,context: str,question: str,chat_history:str) -> str:
        return f"""
You are an AI assistant that answers questions only from the provided document context.

Rules:
- Use only the supplied context.
- Do not use outside knowledge.
- If the answer is not present in the context, reply:
  "I couldn't find that information in the uploaded documents."
- Be concise and factual.
- If multiple context sections contribute to the answer, combine them naturally.

Previous Conversation:
{chat_history}

Context:

{context}

Question:

{question}

Answer:
"""

    async def answer(self,question: str,
                     owner_uid: UUID,session: AsyncSession,
                     dataset_uid: UUID | None = None,session_uid: UUID| None = None):

          
          docs = await self.retriever.retrieve(query=question,
          owner_uid=owner_uid,dataset_uid=dataset_uid,top_k=5)

          chat_session = await self.chat_service.get_or_create_session(
              session=session,owner_uid=owner_uid,
              dataset_uid=dataset_uid,chat_type=ChatType.RAG,session_uid=session_uid,)
          
          if not docs:
                return RAGResponse(session_uid=session_uid,
                    answer="No relevant information found.",
                           sources = [])
    
          context = self.build_context(docs)

          chat_history = await self.chat_service.build_chat_history(session=session,session_uid=chat_session.uid,
                                                                    conversation_limit=5,)
          
          prompt = self.build_prompt(
               context=context,
               question=question,chat_history=chat_history,)

          response = await self.llm.ainvoke(prompt)
          content = response.content

          if isinstance(content, list):
            answer = "".join(
            item["text"]
            for item in content
             if isinstance(item, dict) and item.get("type") == "text")
          else:
           answer = content
          sources = []

          await self.chat_service.save_user_message(session=session,session_uid=chat_session.uid,
                                                    message=question,)
          
          for doc in docs:
            sources.append(SourceResponse(document_uid=doc.metadata["document_uid"],
            document_name=doc.metadata["document_name"],page=doc.metadata["page"],
            chunk_index=doc.metadata["chunk_index"]))
          clean_answer = self.clean_answer(answer)
          await self.chat_service.save_assistant_message(session=session,session_uid=chat_session.uid
                                                         ,message=clean_answer,)
          return RAGResponse(
                        session_uid=chat_session.uid,
                        answer=clean_answer,
                        sources=sources)
          

    def clean_answer(self,text: str) -> str:
        text = text.replace("**", "")
        text = text.replace("__", "")
        text = text.replace("* ", "- ")
        text = re.sub(r"`(.*?)`", r"\1", text)
        return text.strip()
          
          
