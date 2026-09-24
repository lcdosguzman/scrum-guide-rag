from dataclasses import dataclass, field
from typing import Optional

import pytest


@dataclass
class DummyDoc:
    page_content: str
    metadata: dict = field(default_factory=dict)


@pytest.fixture
def doc_factory():
    def make_doc(content: str, metadata: Optional[dict] = None) -> DummyDoc:
        return DummyDoc(content, metadata or {})

    return make_doc


@pytest.fixture
def unsupported_choice_question() -> str:
    return "Que formato obligatorio exige la guia: horas, story points o tallas de camiseta?"


@pytest.fixture
def product_owner_expected_source() -> list[dict[str, list[str]]]:
    return [{"contains": ["Product Owner", "maximiza el valor"]}]
