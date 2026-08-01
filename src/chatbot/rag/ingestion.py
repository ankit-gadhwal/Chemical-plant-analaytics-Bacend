from uuid import uuid4,UUID
from .schemas import DocumentMetadata,DocumentSource
from .chunker import DocumentChunker
from .embeddings import embedding_service
from .loader import DocumentLoader
from .vector_store import VectorStore
from pathlib import Path
from src.db.models import Document
from .retriever import Retriever


class IngestionService:

    def __init__(self):

        self.loader = DocumentLoader()

        self.chunker = DocumentChunker()

        self.embedding_service = embedding_service

        self.vector_store = VectorStore()

        self.retriever = Retriever(embedding_service=self.embedding_service,
                                   vector_store = self.vector_store)
        

    async def ingest_document(
        self,document: Document):
        document_name = Path(document.original_filename).name
        documents = self.loader.load(document.file_path)

        chunks = self.chunker.split_documents(documents)

        texts = [
            chunk.page_content
            for chunk in chunks
        ]

        embeddings = self.embedding_service.embed_documents(
            texts
        )

        ids = [
            str(uuid4())
            for _ in chunks
        ]

        metadatas = []

        for index,chunk in enumerate(chunks):
            metadata = DocumentMetadata(
                owner_uid= str(document.owner_uid),
                dataset_uid= str(document.dataset_uid),
                document_uid= str(document.uid),
                document_name=document_name,
                document_source=DocumentSource.USER,
                page= int(chunk.metadata.get("page")),
                chunk_index=index
            )

            metadatas.append(metadata.model_dump(exclude_none=True))


        self.vector_store.add_documents(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)