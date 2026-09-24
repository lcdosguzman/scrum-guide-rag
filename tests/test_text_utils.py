import pytest

from scrum_rag.text_utils import normalize


@pytest.mark.parametrize(
    ("raw_text", "expected"),
    [
        ("  Scrum   MASTER\nGuide  ", "scrum master guide"),
        ("Product\tOwner", "product owner"),
        ("", ""),
    ],
)
def test_normalize(raw_text, expected):
    assert normalize(raw_text) == expected
