"""Fixtures shared across parser tests."""
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="session")
def fx():
    """Return a helper that gives the bytes of a fixture .docx by name."""
    def _read(name: str) -> bytes:
        return (FIXTURES / name).read_bytes()
    return _read


@pytest.fixture(scope="session")
def empty_docx(fx):
    return fx("empty.docx")

@pytest.fixture(scope="session")
def paragraphs_docx(fx):
    return fx("paragraphs.docx")

@pytest.fixture(scope="session")
def formatting_docx(fx):
    return fx("formatting.docx")

@pytest.fixture(scope="session")
def table_simple_docx(fx):
    return fx("table_simple.docx")

@pytest.fixture(scope="session")
def table_merged_docx(fx):
    return fx("table_merged.docx")

@pytest.fixture(scope="session")
def list_bullet_docx(fx):
    return fx("list_bullet.docx")

@pytest.fixture(scope="session")
def list_numbered_docx(fx):
    return fx("list_numbered.docx")

@pytest.fixture(scope="session")
def list_nested_docx(fx):
    return fx("list_nested.docx")

@pytest.fixture(scope="session")
def image_inline_docx(fx):
    return fx("image_inline.docx")

@pytest.fixture(scope="session")
def mixed_docx(fx):
    return fx("mixed.docx")
