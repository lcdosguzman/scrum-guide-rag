from rich.console import Console
from rich.panel import Panel

from scrum_rag.rag import ScrumRag, format_sources

console = Console()


def main() -> None:
    try:
        rag = ScrumRag()
    except FileNotFoundError as error:
        console.print(f"[red]{error}[/red]")
        return

    console.print(Panel("RAG Scrum listo. Escribe /exit para salir.", title="Chat"))
    last_sources = ""

    while True:
        question = console.input("\n[bold cyan]Tu pregunta:[/bold cyan] ").strip()
        if question in {"/exit", "/quit"}:
            break
        if question == "/sources":
            console.print(last_sources or "Todavia no hay fuentes.")
            continue
        if not question:
            continue

        result = rag.ask(question)
        last_sources = format_sources(result.sources)

        console.print(Panel(result.answer, title="Respuesta"))
        console.print(Panel(last_sources, title="Fuentes recuperadas"))


if __name__ == "__main__":
    main()
