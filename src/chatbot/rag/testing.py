# from uuid import uuid4

# from src.chatbot.rag.embeddings import EmbeddingsService
# from .vector_store import VectorStore

# embedding_service = EmbeddingsService()
# vector_store = VectorStore()

# document = "Pump P101 pressure is 300 PSI."

# embedding = embedding_service.embed_documents(
#     [document]
# )

# vector_store.add_documents(
#     ids=[str(uuid4())],
#     documents=[document],
#     embeddings=embedding,
#     metadatas=[
#         {
#             "source": "system",
#             "document": "pump_manual.pdf",
#         }
#     ],
# )

# print(vector_store.count())

# query = embedding_service.embed_query(
#     "Which pump has the highest pressure?"
# )

# results = vector_store.similarity_search(query)

# print(results["documents"][0][0])



# from .loader import DocumentLoader
# from .chunker import DocumentChunker

# loader = DocumentLoader()
# chunker = DocumentChunker()

# documents = loader.load(
#     "storage/manuals/1-s2.0-S156849462501556X-main.pdf"
# )

# chunks = chunker.split_documents(documents)

# print(f"Pages : {len(documents)}")
# print(f"Chunks: {len(chunks)}")

# print(len(documents))
# print(documents[0].page_content[:23])

# print(documents[0].metadata)

# import asyncio

# from .ingestion import IngestionService

# ingestion = IngestionService()


# async def main():
#     count = await ingestion.ingest_document(
#         "storage/manuals/dl-curriculum.pdf"
#     )
#     print(count)


# if __name__ == "__main__":
#     asyncio.run(main())

from .vector_store import VectorStore
vector_store = VectorStore()
vector_store.reset_collection()

print(vector_store.count())   # Should print 0