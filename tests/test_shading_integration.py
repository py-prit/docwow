"""Round-trip integration tests for paragraph and table cell shading.

Verifies:
  DOCX → parse → HTML → parse → DOCX → re-parse
  shading survives the full pipeline unchanged.
"""
from __future__ import annotations

from pathlib import Path

import docwow
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.models.table import Table, TableCell, TableRow
from docwow.models.document import Document
from docwow.renderer.html_renderer import render_document as render_html
from docwow.html_parser.html_parser import parse_html
from docwow.writer.docx_writer import write_docx
from docwow.parser.docx_parser import parse_docx

FIXTURES = Path(__file__).parent / "fixtures"


def _doc(*body):
    return Document(
        body=body,
        styles=(),
        numbering=(),
        page_width_pt=595.28, page_height_pt=841.89,
        margin_top_pt=72.0, margin_bottom_pt=72.0,
        margin_left_pt=72.0, margin_right_pt=72.0,
    )


def _round_trip(doc: Document) -> Document:
    html = render_html(doc)
    rt_doc = parse_html(html)
    docx_bytes = write_docx(rt_doc)
    return parse_docx(docx_bytes)


class TestParagraphShadingRoundTrip:
    def test_paragraph_shading_survives_round_trip(self):
        fmt = ParagraphFormatting(shading="4472C4")
        para = Paragraph(runs=(TextRun(text="Blue background"),), formatting=fmt)
        doc = _doc(para)
        final = _round_trip(doc)
        assert final.body[0].formatting.shading == "4472C4"

    def test_no_shading_survives_round_trip(self):
        fmt = ParagraphFormatting()
        para = Paragraph(runs=(TextRun(text="Plain"),), formatting=fmt)
        doc = _doc(para)
        final = _round_trip(doc)
        assert final.body[0].formatting.shading is None


class TestTableCellShadingRoundTrip:
    def test_cell_shading_survives_round_trip(self):
        cell = TableCell(
            paragraphs=(Paragraph(runs=(TextRun(text="Orange"),), formatting=ParagraphFormatting()),),
            shading="ED7D31",
        )
        table = Table(rows=(TableRow(cells=(cell,)),))
        doc = _doc(table)
        final = _round_trip(doc)
        assert final.body[0].rows[0].cells[0].shading == "ED7D31"

    def test_no_cell_shading_survives_round_trip(self):
        cell = TableCell(
            paragraphs=(Paragraph(runs=(TextRun(text="Plain"),), formatting=ParagraphFormatting()),),
        )
        table = Table(rows=(TableRow(cells=(cell,)),))
        doc = _doc(table)
        final = _round_trip(doc)
        assert final.body[0].rows[0].cells[0].shading is None


class TestShadingFixtureRoundTrip:
    """Parse the real shading.docx fixture and check values survive a round-trip."""

    def test_shading_docx_fixture_round_trip(self):
        data = (FIXTURES / "shading.docx").read_bytes()
        doc = parse_docx(data)

        # Verify parse
        para0 = doc.body[0]
        assert isinstance(para0, Paragraph)
        assert para0.formatting.shading == "4472C4"

        table = doc.body[2]
        assert isinstance(table, Table)
        assert table.rows[0].cells[0].shading == "ED7D31"

        # Full round-trip
        html = render_html(doc)
        rt_doc = parse_html(html)
        docx_bytes = write_docx(rt_doc)
        final = parse_docx(docx_bytes)

        assert final.body[0].formatting.shading == "4472C4"
        assert final.body[2].rows[0].cells[0].shading == "ED7D31"


class TestShadingPublicApi:
    """Verify the public docwow.open() API exposes shading correctly."""

    def test_open_exposes_paragraph_shading(self):
        data = (FIXTURES / "shading.docx").read_bytes()
        wrapper = docwow.open(data)
        para = wrapper.paragraphs[0]
        assert para.shading == "4472C4"

    def test_open_exposes_cell_shading(self):
        data = (FIXTURES / "shading.docx").read_bytes()
        wrapper = docwow.open(data)
        # Table is the 3rd element (index 2)
        from docwow.api.table import MutableTable
        table = None
        for item in wrapper.paragraphs:
            if isinstance(item, MutableTable):
                table = item
                break
        assert table is not None
        assert table[0][0].shading == "ED7D31"
