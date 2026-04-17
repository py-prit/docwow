"""Tests for shading parsing from DOCX (paragraph and table cell)."""

from __future__ import annotations

from pathlib import Path
import pytest

from docwow.parser.docx_parser import parse_docx
from docwow.models.paragraph import Paragraph
from docwow.models.table import Table

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="module")
def shading_doc():
    data = (FIXTURES / "shading.docx").read_bytes()
    return parse_docx(data)


class TestParagraphShadingParser:
    def test_shaded_paragraph_has_shading(self, shading_doc):
        para = shading_doc.body[0]
        assert isinstance(para, Paragraph)
        assert para.formatting.shading == "4472C4"

    def test_plain_paragraph_has_no_shading(self, shading_doc):
        para = shading_doc.body[1]
        assert isinstance(para, Paragraph)
        assert para.formatting.shading is None


class TestTableCellShadingParser:
    def test_orange_cell_has_shading(self, shading_doc):
        table = shading_doc.body[2]
        assert isinstance(table, Table)
        cell = table.rows[0].cells[0]
        assert cell.shading == "ED7D31"

    def test_plain_cell_has_no_shading(self, shading_doc):
        table = shading_doc.body[2]
        assert isinstance(table, Table)
        cell = table.rows[0].cells[1]
        assert cell.shading is None
