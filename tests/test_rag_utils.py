import pytest

from scrum_rag.rag import query_terms, unique_docs


@pytest.mark.parametrize(
    ("question", "expected_terms"),
    [
        ("Que dice la guia sobre OOPSLA?", {"OOPSLA", "oopsla"}),
        ("que es un rol", set()),
        ("Diferencia entre Product Goal y Sprint Goal", {"Product", "product", "Sprint", "sprint"}),
    ],
)
def test_query_terms(question, expected_terms):
    assert expected_terms.issubset(set(query_terms(question)))


def test_unique_docs_deduplicates_by_source_page_and_content_prefix(doc_factory):
    first = doc_factory("same content", {"source": "guide.pdf", "page": 1})
    duplicate = doc_factory("same content", {"source": "guide.pdf", "page": 1})
    other = doc_factory("other content", {"source": "guide.pdf", "page": 2})

    assert unique_docs([first, duplicate, other]) == [first, other]
