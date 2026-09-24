import pytest

from scrum_rag.guardrails import (
    extract_choice_options,
    has_supported_choice,
    needs_supported_choice,
    should_block_unsupported_choice,
)


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "Que formato obligatorio exige la guia: horas, story points o tallas de camiseta?",
            ["story points", "tallas de camiseta"],
        ),
        (
            "Que herramienta recomienda la guia: Jira, Trello o Azure DevOps?",
            ["trello", "azure devops"],
        ),
        ("Que es Scrum?", []),
    ],
)
def test_extract_choice_options(question, expected):
    assert extract_choice_options(question) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "Que formato obligatorio exige la guia: horas, story points o tallas de camiseta?",
            True,
        ),
        ("Que prefieres: horas, story points o tallas de camiseta?", False),
        ("Que es Scrum?", False),
    ],
)
def test_needs_supported_choice(question, expected):
    assert needs_supported_choice(question) is expected


def test_has_supported_choice_when_option_appears_in_context(
    doc_factory,
    unsupported_choice_question,
):
    docs = [doc_factory("Los Developers pueden usar story points si el equipo lo decide.")]

    assert has_supported_choice(unsupported_choice_question, docs) is True


def test_should_block_unsupported_choice_when_no_option_is_supported(
    doc_factory,
    unsupported_choice_question,
):
    docs = [doc_factory("La Guia de Scrum no prescribe una tecnica especifica de estimacion.")]

    assert should_block_unsupported_choice(unsupported_choice_question, docs) is True
