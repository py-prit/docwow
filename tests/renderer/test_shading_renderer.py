"""Tests for shading rendering in paragraphs and table cells."""

from __future__ import annotations

from docwow.models.paragraph import Paragraph
from docwow.models.styles import ParagraphFormatting
from docwow.models.table import Table, TableCell, TableRow
from docwow.renderer.paragraph_renderer import render_paragraph
from docwow.renderer.table_renderer import render_table


class TestParagraphShadingRenderer:
    def test_shading_emits_data_attr(self):
        fmt = ParagraphFormatting(shading="4472C4")
        para = Paragraph(runs=(), formatting=fmt)
        html = render_paragraph(para)
        assert 'data-dw-shading="4472C4"' in html

    def test_shading_emits_background_color_style(self):
        fmt = ParagraphFormatting(shading="4472C4")
        para = Paragraph(runs=(), formatting=fmt)
        html = render_paragraph(para)
        assert "background-color:#4472C4" in html

    def test_no_shading_omits_data_attr(self):
        fmt = ParagraphFormatting()
        para = Paragraph(runs=(), formatting=fmt)
        html = render_paragraph(para)
        assert "data-dw-shading" not in html

    def test_no_shading_omits_background_color(self):
        fmt = ParagraphFormatting()
        para = Paragraph(runs=(), formatting=fmt)
        html = render_paragraph(para)
        assert "background-color" not in html


class TestTableCellShadingRenderer:
    def _make_table(self, shading: str | None) -> str:
        cell = TableCell(paragraphs=(), shading=shading)
        row = TableRow(cells=(cell,))
        table = Table(rows=(row,))
        return render_table(table)

    def test_shading_emits_data_attr(self):
        html = self._make_table("ED7D31")
        assert 'data-dw-shading="ED7D31"' in html

    def test_shading_emits_background_color_style(self):
        html = self._make_table("ED7D31")
        assert "background-color:#ED7D31" in html

    def test_no_shading_omits_data_attr(self):
        html = self._make_table(None)
        assert "data-dw-shading" not in html
