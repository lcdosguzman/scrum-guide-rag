from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings

from scrum_rag.config import CHAT_MODEL, DB_DIR, EMBEDDING_MODEL, RETRIEVAL_K
from scrum_rag.guardrails import UNSUPPORTED_CHOICE_ANSWER, should_block_unsupported_choice

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente experto en Scrum. Responde en espanol usando solo el contexto dado. "
            "No uses conocimiento externo. Si el contexto no contiene evidencia suficiente, dilo claramente. "
            "Si la pregunta ofrece opciones, no elijas una opcion a menos que el contexto la respalde explicitamente. "
            "Si ninguna opcion esta respaldada por el contexto, responde que la Guia de Scrum no lo especifica. "
            "Cuando respondas, menciona las fuentes relevantes entre corchetes, por ejemplo [Fuente 1].",
        ),
        (
            "human",
            "Contexto:\n{context}\n\nPregunta:\n{question}",
        ),
    ]
)


@dataclass(frozen=True)
class Source:
    index: int
    source: str
    page: Optional[int]
    preview: str


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[Source]
    contexts: list[str]


def format_context(docs) -> str:
    return "\n\n".join(
        f"[Fuente {index}] {doc.page_content}" for index, doc in enumerate(docs, start=1)
    )


def build_sources(docs) -> list[Source]:
    sources = []
    for index, doc in enumerate(docs, start=1):
        raw_source = doc.metadata.get("source", "fuente desconocida")
        page = doc.metadata.get("page")
        display_page = page + 1 if isinstance(page, int) else None
        preview = " ".join(doc.page_content.split())[:240]
        sources.append(
            Source(
                index=index,
                source=Path(raw_source).name,
                page=display_page,
                preview=preview,
            )
        )
    return sources


def format_sources(sources: list[Source]) -> str:
    lines = []
    for source in sources:
        page_text = f", pagina {source.page}" if source.page else ""
        lines.append(f"[{source.index}] {source.source}{page_text}")
    return "\n".join(lines)


def unique_docs(docs):
    seen = set()
    unique = []
    for doc in docs:
        key = (
            doc.metadata.get("source"),
            doc.metadata.get("page"),
            doc.page_content[:120],
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(doc)
    return unique


def query_terms(query: str) -> list[str]:
    cleaned = query.replace("?", " ").replace("¿", " ").replace(".", " ").replace(",", " ")
    terms = []
    for term in cleaned.split():
        if len(term) >= 5 or term.isupper():
            terms.extend([term, term.lower(), term.upper()])
    return list(dict.fromkeys(terms))


class ScrumRag:
    def __init__(self) -> None:
        if not DB_DIR.exists():
            raise FileNotFoundError(
                "Todavia no existe el indice. Ejecuta primero: python3 -m scrum_rag.ingest"
            )

        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vector_store = Chroma(
            persist_directory=str(DB_DIR),
            embedding_function=embeddings,
        )
        self.vector_store = vector_store
        self.llm = ChatOllama(model=CHAT_MODEL, temperature=0)

    def ask(self, question: str) -> RagAnswer:
        docs = self.retrieve(question)
        contexts = [doc.page_content for doc in docs]
        sources = build_sources(docs)

        if should_block_unsupported_choice(question, docs):
            return RagAnswer(
                answer=UNSUPPORTED_CHOICE_ANSWER,
                sources=sources,
                contexts=contexts,
            )

        prompt = PROMPT.invoke(
            {
                "context": format_context(docs),
                "question": question,
            }
        )
        answer = self.llm.invoke(prompt)
        return RagAnswer(answer=answer.content, sources=sources, contexts=contexts)

    def retrieve(self, query: str, k: int = RETRIEVAL_K):
        semantic_docs = self.vector_store.similarity_search(query, k=k)
        keyword_docs = []

        for term in query_terms(query):
            keyword_docs.extend(
                self.vector_store.similarity_search(
                    query,
                    k=2,
                    where_document={"$contains": term},
                )
            )

        return unique_docs(keyword_docs + semantic_docs)[:k]

    def search(self, query: str, k: int = RETRIEVAL_K):
        semantic_results = self.vector_store.similarity_search_with_score(query, k=k)
        keyword_results = []

        for term in query_terms(query):
            docs = self.vector_store.similarity_search(
                query,
                k=2,
                where_document={"$contains": term},
            )
            keyword_results.extend((doc, None) for doc in docs)

        seen = set()
        results = []
        for doc, score in keyword_results + semantic_results:
            key = (
                doc.metadata.get("source"),
                doc.metadata.get("page"),
                doc.page_content[:120],
            )
            if key in seen:
                continue
            seen.add(key)
            results.append((doc, score))
            if len(results) >= k:
                break

        return results
