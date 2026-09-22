import shutil

from rich.console import Console

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from scrum_rag.config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR, DB_DIR, EMBEDDING_MODEL
from scrum_rag.loaders import load_documents

console = Console()


def main() -> None:
    documents = load_documents(DATA_DIR)
    if not documents:
        console.print(f"[red]No encontre documentos en {DATA_DIR}.[/red]")
        console.print("Copia ahi la Guia de Scrum en PDF, TXT o Markdown y vuelve a ejecutar.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)

    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(DB_DIR),
    )

    console.print(f"[green]Indexados {len(chunks)} fragmentos desde {len(documents)} paginas/documentos.[/green]")
    console.print(f"Base vectorial guardada en: {DB_DIR}")


if __name__ == "__main__":
    main()
