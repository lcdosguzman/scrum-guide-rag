from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document


def load_documents(data_dir: Path) -> list[Document]:
    documents: list[Document] = []

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            documents.extend(PyPDFLoader(str(path)).load())
        elif suffix in {".txt", ".md"}:
            documents.extend(TextLoader(str(path), encoding="utf-8").load())

    return documents
