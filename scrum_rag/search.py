import argparse

from rich.console import Console
from rich.panel import Panel

from scrum_rag.rag import ScrumRag

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspecciona que fragmentos recupera el RAG.")
    parser.add_argument("query", help="Texto de busqueda")
    parser.add_argument("--k", type=int, default=6, help="Cantidad de fragmentos a recuperar")
    args = parser.parse_args()

    rag = ScrumRag()
    results = rag.search(args.query, k=args.k)

    for index, (doc, score) in enumerate(results, start=1):
        source = doc.metadata.get("source", "fuente desconocida")
        page = doc.metadata.get("page")
        page_text = f"pagina {page + 1}" if isinstance(page, int) else "pagina desconocida"
        score_text = "keyword" if score is None else f"score={score:.4f}"
        text = " ".join(doc.page_content.split())
        console.print(
            Panel(
                text[:1200],
                title=f"[{index}] {score_text} | {source} | {page_text}",
            )
        )


if __name__ == "__main__":
    main()
