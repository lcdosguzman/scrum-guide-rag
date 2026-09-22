import argparse
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.table import Table

from scrum_rag.config import CHAT_MODEL, CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, RETRIEVAL_K
from scrum_rag.rag import ScrumRag

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "eval" / "golden_dataset.jsonl"
REPORTS_DIR = PROJECT_ROOT / "eval" / "reports"

ABSTENTION_MARKERS = [
    "no tengo informacion suficiente",
    "no tengo información suficiente",
    "no encuentro",
    "no contiene",
    "no puedo determinar",
    "no hay informacion",
    "no hay información",
    "no especifica",
    "no esta especificada",
    "no está especificada",
    "no esta presente",
    "no está presente",
    "no proporciona",
    "no menciona",
    "no se menciona",
    "no se menciona explicitamente",
    "no se menciona explícitamente",
]

console = Console()


@dataclass(frozen=True)
class EvalResult:
    case: dict[str, Any]
    answer: Optional[str]
    retrieved_contexts: list[str]
    retrieved_sources: list[dict[str, Any]]
    latency_seconds: float
    hit: bool
    precision_at_k: float
    reciprocal_rank: float
    answer_terms_score: Optional[float]
    abstention_correct: Optional[bool]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua el RAG contra un golden dataset.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--retrieval-only", action="store_true", help="No llama al modelo generativo.")
    parser.add_argument("--k", type=int, default=RETRIEVAL_K)
    args = parser.parse_args()

    cases = load_dataset(args.dataset)
    rag = ScrumRag()

    results = []
    for case in cases:
        started = time.perf_counter()
        try:
            docs = rag.retrieve(case["question"], k=args.k)
            answer = None
            if not args.retrieval_only:
                answer = rag.ask(case["question"]).answer
        except Exception as error:
            console.print("[red]No se pudo ejecutar la evaluacion.[/red]")
            console.print("Verifica que Ollama este abierto y que los modelos esten descargados:")
            console.print("  ollama pull llama3.2")
            console.print("  ollama pull nomic-embed-text")
            console.print(f"Detalle: {error}")
            raise SystemExit(1)
        latency = time.perf_counter() - started
        results.append(evaluate_case(case, docs, answer, latency))

    summary = summarize(results)
    render_summary(summary, results)
    write_reports(summary, results, args)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def evaluate_case(case: dict[str, Any], docs, answer: Optional[str], latency: float) -> EvalResult:
    relevant_positions = [
        index
        for index, doc in enumerate(docs, start=1)
        if is_relevant(doc, case.get("expected_sources", []))
    ]
    relevant_count = len(relevant_positions)
    hit = relevant_count > 0 if case.get("should_answer", True) else True
    reciprocal_rank = 1 / relevant_positions[0] if relevant_positions else 0.0
    precision_at_k = relevant_count / len(docs) if docs else 0.0

    answer_terms_score = None
    abstention_correct = None
    if answer is not None:
        if case.get("should_answer", True):
            answer_terms_score = term_coverage(answer, case.get("expected_answer_terms", []))
        else:
            abstention_correct = contains_abstention(answer)

    return EvalResult(
        case=case,
        answer=answer,
        retrieved_contexts=[doc.page_content for doc in docs],
        retrieved_sources=[source_payload(doc, index) for index, doc in enumerate(docs, start=1)],
        latency_seconds=latency,
        hit=hit,
        precision_at_k=precision_at_k,
        reciprocal_rank=reciprocal_rank,
        answer_terms_score=answer_terms_score,
        abstention_correct=abstention_correct,
    )


def is_relevant(doc, expected_sources: list[dict[str, Any]]) -> bool:
    if not expected_sources:
        return False

    text = normalize(doc.page_content)

    for expected in expected_sources:
        expected_terms = expected.get("contains", [])
        if all(normalize(term) in text for term in expected_terms):
            return True

    return False


def source_payload(doc, index: int) -> dict[str, Any]:
    page = doc.metadata.get("page")
    display_page = page + 1 if isinstance(page, int) else None
    source = doc.metadata.get("source", "fuente desconocida")
    return {
        "index": index,
        "source": Path(source).name,
        "page": display_page,
        "preview": " ".join(doc.page_content.split())[:300],
    }


def term_coverage(answer: str, terms: list[str]) -> float:
    if not terms:
        return 1.0
    answer_text = normalize(answer)
    matches = sum(1 for term in terms if normalize(term) in answer_text)
    return matches / len(terms)


def contains_abstention(answer: str) -> bool:
    answer_text = normalize(answer)
    return any(marker in answer_text for marker in ABSTENTION_MARKERS)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def summarize(results: list[EvalResult]) -> dict[str, Any]:
    answerable = [result for result in results if result.case.get("should_answer", True)]
    unanswerable = [result for result in results if not result.case.get("should_answer", True)]
    term_scores = [
        result.answer_terms_score
        for result in answerable
        if result.answer_terms_score is not None
    ]
    abstention_values = [
        result.abstention_correct
        for result in unanswerable
        if result.abstention_correct is not None
    ]

    return {
        "total_cases": len(results),
        "answerable_cases": len(answerable),
        "unanswerable_cases": len(unanswerable),
        "hit_rate": average([result.hit for result in answerable]),
        "precision_at_k": average([result.precision_at_k for result in answerable]),
        "mrr": average([result.reciprocal_rank for result in answerable]),
        "answer_term_coverage": average(term_scores),
        "abstention_accuracy": average(abstention_values),
        "latency_avg_seconds": average([result.latency_seconds for result in results]),
        "latency_p95_seconds": percentile([result.latency_seconds for result in results], 95),
        "config": {
            "chat_model": CHAT_MODEL,
            "embedding_model": EMBEDDING_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "retrieval_k": RETRIEVAL_K,
        },
    }


def average(values) -> Optional[float]:
    values = [float(value) for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def percentile(values: list[float], percent: int) -> Optional[float]:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100)[percent - 1]


def render_summary(summary: dict[str, Any], results: list[EvalResult]) -> None:
    table = Table(title="RAG Evaluation")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key in [
        "total_cases",
        "hit_rate",
        "precision_at_k",
        "mrr",
        "answer_term_coverage",
        "abstention_accuracy",
        "latency_avg_seconds",
        "latency_p95_seconds",
    ]:
        table.add_row(key, format_metric(summary.get(key)))
    console.print(table)

    failures = [result for result in results if is_failure(result)]
    if failures:
        console.print("\n[bold red]Casos a revisar[/bold red]")
        for result in failures:
            console.print(f"- {result.case['id']}: {result.case['question']}")


def is_failure(result: EvalResult) -> bool:
    if result.case.get("should_answer", True):
        return not result.hit
    if result.abstention_correct is None:
        return False
    return not result.abstention_correct


def format_metric(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.3f}"


def write_reports(summary: dict[str, Any], results: list[EvalResult], args) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    mode = "retrieval" if args.retrieval_only else "full"
    json_path = REPORTS_DIR / f"{timestamp}-{mode}.json"
    md_path = REPORTS_DIR / f"{timestamp}-{mode}.md"

    payload = {
        "summary": summary,
        "results": [result_to_dict(result) for result in results],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    console.print(f"\nReporte JSON: {json_path}")
    console.print(f"Reporte Markdown: {md_path}")


def result_to_dict(result: EvalResult) -> dict[str, Any]:
    return {
        "id": result.case["id"],
        "category": result.case.get("category"),
        "question": result.case["question"],
        "should_answer": result.case.get("should_answer", True),
        "answer": result.answer,
        "retrieved_sources": result.retrieved_sources,
        "latency_seconds": result.latency_seconds,
        "metrics": {
            "hit": result.hit,
            "precision_at_k": result.precision_at_k,
            "reciprocal_rank": result.reciprocal_rank,
            "answer_terms_score": result.answer_terms_score,
            "abstention_correct": result.abstention_correct,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = ["# RAG Evaluation Report", "", "## Summary", ""]
    for key, value in payload["summary"].items():
        if key == "config":
            continue
        lines.append(f"- **{key}**: {format_metric(value)}")
    lines.extend(["", "## Config", ""])
    for key, value in payload["summary"]["config"].items():
        lines.append(f"- **{key}**: `{value}`")
    lines.extend(["", "## Cases", ""])
    for result in payload["results"]:
        metrics = result["metrics"]
        lines.extend(
            [
                f"### {result['id']} - {result['category']}",
                "",
                f"**Question:** {result['question']}",
                "",
                f"**Hit:** {metrics['hit']}",
                f"**Precision@K:** {format_metric(metrics['precision_at_k'])}",
                f"**MRR contribution:** {format_metric(metrics['reciprocal_rank'])}",
                "",
            ]
        )
        if result["answer"]:
            lines.extend(["**Answer:**", "", result["answer"], ""])
        lines.append("**Retrieved sources:**")
        for source in result["retrieved_sources"]:
            page = f", page {source['page']}" if source["page"] else ""
            lines.append(f"- [{source['index']}] {source['source']}{page}: {source['preview']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
