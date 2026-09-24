import pytest

from scrum_rag.evaluate import is_relevant, term_coverage


@pytest.mark.parametrize(
    ("answer", "terms", "expected"),
    [
        (
            "Scrum se basa en empirismo y pensamiento Lean.",
            ["empirismo", "pensamiento Lean", "transparencia"],
            2 / 3,
        ),
        ("anything", [], 1.0),
    ],
)
def test_term_coverage(answer, terms, expected):
    assert term_coverage(answer, terms) == expected


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("El Product Owner maximiza el valor y gestiona el Product Backlog.", True),
        ("El Scrum Master sirve al Scrum Team.", False),
    ],
)
def test_is_relevant(content, expected, doc_factory, product_owner_expected_source):
    doc = doc_factory(content)

    assert is_relevant(doc, product_owner_expected_source) is expected
