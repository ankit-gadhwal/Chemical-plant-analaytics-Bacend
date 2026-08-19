import os
from typing import List
import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document
import uuid

class VectorStore:

    COLLECTION_NAME = "chemical_equipment"

    def __init__(self, presist_directory: str | None = None):
        if presist_directory is None:
            presist_directory = os.getenv("CHROMA_PERSIST_DIR", "storage/chroma")
        self.client = chromadb.PersistentClient(
            path=presist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(name=self.COLLECTION_NAME,
            metadata={
                "description": "Chemical Equipment Knowledge Base"
            })

    def add_documents(self,ids: List[str],documents: List[str],
                      embeddings: List[List[float]],metadatas: List[dict],):
        
        self.collection.add(ids=ids,documents=documents,
                embeddings=embeddings,metadatas=metadatas,)

    def similarity_search(self,
                          query_embedding: List[float],where:dict,top_k: int = 5) -> list[Document]:

        results = self.collection.query(query_embeddings=[query_embedding],n_results=top_k,where=where)

        documents = []

        docs = results.get("documents",[[]])[0]
        metadatas = results.get("metadatas",[[]])[0]

        for text,metadata in zip(docs,metadatas):
            documents.append(Document(
                page_content=text,
                metadata=metadata
            ))

        return documents


    def delete_by_document(self,document_uid: uuid.UUID):
        print("Before:", self.collection.count())
        self.collection.delete(where={"document_uid": str(document_uid)})
        print("After:", self.collection.count())

    def count(self):
        return self.collection.count()


    def reset_collection(self):
        self.client.delete_collection(self.COLLECTION_NAME)

        self.collection = self.client.get_or_create_collection(
        name=self.COLLECTION_NAME,
        metadata={
            "description": "Chemical Equipment Knowledge Base"
        })