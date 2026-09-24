import re

from scrum_rag.text_utils import normalize

UNSUPPORTED_CHOICE_ANSWER = (
    "La Guia de Scrum no especifica ninguna de esas opciones en el contexto recuperado. "
    "No puedo elegir un formato obligatorio sin evidencia en la guia."
)


def extract_choice_options(question: str) -> list[str]:
    if ":" not in question:
        return []

    options_text = question.split(":", maxsplit=1)[1]
    options = re.split(r",|\bo\b", options_text, flags=re.IGNORECASE)
    return [
        normalize(option.strip(" ?.¿!¡"))
        for option in options
        if len(normalize(option.strip(" ?.¿!¡"))) >= 6
    ]


def needs_supported_choice(question: str) -> bool:
    text = normalize(question)
    markers = ["obligatorio", "obligatoria", "exige", "recomienda", "debe usar"]
    return bool(extract_choice_options(question)) and any(marker in text for marker in markers)


def has_supported_choice(question: str, docs) -> bool:
    options = extract_choice_options(question)
    context = normalize("\n".join(doc.page_content for doc in docs))
    return any(option in context for option in options)


def should_block_unsupported_choice(question: str, docs) -> bool:
    """Custom hallucination guardrail for option-list questions.

    This is not a standard RAG component. It exists because small local LLMs can
    feel pressured to choose one option from a question even when the retrieved
    context does not support any of them.
    """
    return needs_supported_choice(question) and not has_supported_choice(question, docs)
