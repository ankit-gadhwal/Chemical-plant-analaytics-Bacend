import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile,status
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from src.chatbot.rag.ingestion import IngestionService
from src.datasets.service import DatasetService
import os
from src.db.models import Document
from .repository import DocumentRepository
from .schemas import DocumentResponse
from sqlalchemy import select
from src.chatbot.rag.vector_store import VectorStore
UPLOAD_DIRECTORY = Path("storage/documents")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


class DocumentService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.document_repository = DocumentRepository(session)
        self.dataset_service = DatasetService()
        self.vector_store = VectorStore()
        self.ingestion_service = None

    async def upload_document(
        self,
        dataset_uid: uuid.UUID,
        file: UploadFile,
        current_user,
    ) -> DocumentResponse:

        dataset = await self.dataset_service.get_dataset(dataset_uid,self.session)

        if dataset is None:
                     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found.")
        
        if dataset.owner_uid != current_user.uid:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this dataset."
            )

        extension = Path(file.filename).suffix

        stored_filename = f"{uuid.uuid4()}{extension}"

        file_path = UPLOAD_DIRECTORY / stored_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document = Document(
            dataset_uid=dataset.uid,
            owner_uid=current_user.uid,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
        )

        document = await self.document_repository.create(document)

        if self.ingestion_service is None:
             self.ingestion_service = IngestionService()

        res = await self.ingestion_service.ingest_document(
            document
        )
        print(res)

        return DocumentResponse.model_validate(document)



    async def get_document(self,document_uid: uuid.UUID,
                           current_user,) -> DocumentResponse:

        document = await self.document_repository.get_by_uid(document_uid)

        if document is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found.")

        if document.owner_uid != current_user.uid:
            raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to access this document."
    )

        return DocumentResponse.model_validate(document)


    async def get_documents_by_dataset(
        self,
        dataset_uid: uuid.UUID,
        current_user,
    ):
        dataset = await self.dataset_service.get_dataset(
            dataset_uid,
            self.session,
        )

        if dataset.owner_uid != current_user.uid:
            raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to access this document.")

        documents = await self.document_repository.get_by_dataset(
            dataset_uid
        )
        if documents is None:
                
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                                     detail="Document not found.")
        return [
            DocumentResponse.model_validate(document)
            for document in documents
        ]

    async def delete_document(
        self,
        document_uid: uuid.UUID,
        current_user,
    ):

        document = await self.document_repository.get_by_uid(
            document_uid
        )

        if document is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                 detail="Document not found.")

        if document.owner_uid != current_user.uid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You are not allowed to access this document.")

        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        self.vector_store.delete_by_document(document_uid)
        await self.document_repository.delete(document)

        return {
            "message": "Document deleted successfully."
        }
