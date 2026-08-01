from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentChunker:
    """
    splits Langchain Documents into smaller chunks for embedding.
    """

    def __init__(self,chunk_size: int = 800,
                 chunk_overlap: int = 150,) -> None:
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                            chunk_overlap=chunk_overlap,
                                                            separators=[
                                                                "\n\n",'\n',". "," ",""])

    def split_documents(self,documents: list[Document]) -> list[Document]:
        """
        split loaded documents into smaller chunks while preserving metadata."""

        return self.text_splitter.split_documents(documents)

    