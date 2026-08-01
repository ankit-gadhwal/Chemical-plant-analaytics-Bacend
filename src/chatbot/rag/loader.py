from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,Docx2txtLoader)
from langchain_core.documents import Document

class DocumentLoader:

    """
    Responsible for loading supported document types.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".docx",
    }

    def load(self,file_path: str) -> list[Document]:

        extension = Path(file_path).suffix.lower()

        if extension == ".pdf":
            loader = PyPDFLoader(file_path)

        elif extension == ".docx":
            loader = Docx2txtLoader(file_path)

        elif extension == ".txt":
            loader = TextLoader(file_path,
                                encoding="utf-8")

        else:
            raise ValueError(f"Unsupported file type : {extension}")

        return loader.load()
    