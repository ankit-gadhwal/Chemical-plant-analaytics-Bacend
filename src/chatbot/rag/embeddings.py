class EmbeddingsService:
    """
    Wrapper around SentenceTransformer.

    Responsible for generating embeddings
    for documents and user queries.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """
        generate embeddings for multiple documents.
        """
        embeddings = self.model.encode(
            documents,
            normalize_embeddings=True,
            convert_to_tensor=True,
        )

        return embeddings.cpu().tolist()

    def embed_query(self, query: str) -> list[float]:
        """Generate embeddings for a single query"""
        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_tensor=True,
        )

        return embedding.cpu().tolist()


embedding_service = EmbeddingsService()

# embedding_service = EmbeddingsService()

# vector = embedding_service.embed_query(
#     "What is pump pressure?"
# )

# print(len(vector))
    
