from uuid import UUID

from langchain_core.documents import Document
from .embeddings import EmbeddingsService
from .vector_store import VectorStore

class Retriever:

    def __init__(self,embedding_service: EmbeddingsService,
                 vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def retrieve(self,query: str,owner_uid:UUID,
                       dataset_uid:UUID | None=None,top_k : int = 5)-> list[Document]:
        """
        Retrieve the most relavant chunks from ChromaDB"""

        query_embedding = self.embedding_service.embed_query(query)

        filters = {"owner_uid": str(owner_uid)}

        if dataset_uid:
            filters = {
                "$and": [
                    {"owner_uid": str(owner_uid)},
                    {"dataset_uid": str(dataset_uid)}
                    ]}
        else:
            filters = {
                "owner_uid": str(owner_uid)
                }

        return self.vector_store.similarity_search(query_embedding=query_embedding,
                                                         where=filters,top_k=top_k)
        