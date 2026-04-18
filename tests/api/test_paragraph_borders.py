"""Tests for paragraph border support (w:pBdr)."""

from __future__ import annotations

import docwow
from docwow.api.document import DocumentWrapper
from docwow.api.paragraph import MutableParagraph
from docwow.models.borders import BorderDef
from docwow.models.styles import ParagraphBorders


def _box_borders(width_pt: float = 0.5, color: str | None = None) -> ParagraphBorders:
    bd = BorderDef(style="single", width_pt=width_pt, color=color)
    return ParagraphBorders(top=bd, left=bd, bottom=bd, right=bd)


class TestParagraphBordersModel:
    def test_default_no_borders(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("hello")
        assert para.borders is None

    def test_set_borders(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("hello")
        borders = _box_borders()
        para.set_borders(borders)
        assert para.borders is borders

    def test_set_borders_chainable(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("hello")
        result = para.set_borders(_box_borders())
        assert result is para

    def test_clear_borders(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("hello")
        para.set_borders(_box_borders())
        para.set_borders(None)
        assert para.borders is None

    def test_partial_borders(self):
        bd = BorderDef(style="single", width_pt=1.0)
        borders = ParagraphBorders(top=bd, bottom=bd)
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("hello")
        para.set_borders(borders)
        assert para.borders.top is bd
        assert para.borders.left is None


class TestParagraphBordersDocxRoundTrip:
    def test_box_border_survives_docx_round_trip(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("bordered")
        para.set_borders(_box_borders(width_pt=1.0))

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = doc2.paragraphs[0]
        assert para2.borders is not None
        assert para2.borders.top is not None
        assert para2.borders.top.style == "single"
        assert abs(para2.borders.top.width_pt - 1.0) < 0.01

    def test_partial_border_survives_docx_round_trip(self):
        bd = BorderDef(style="single", width_pt=0.5)
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("top only")
        para.set_borders(ParagraphBorders(top=bd))

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = doc2.paragraphs[0]
        assert para2.borders is not None
        assert para2.borders.top is not None
        assert para2.borders.left is None

    def test_no_borders_not_written(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("no borders")
        data = doc.to_bytes()
        assert b"pBdr" not in data

    def test_colored_border_survives_round_trip(self):
        bd = BorderDef(style="single", width_pt=1.0, color="FF0000")
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("red border")
        para.set_borders(ParagraphBorders(top=bd, bottom=bd))

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = doc2.paragraphs[0]
        assert para2.borders.top.color == "FF0000"


class TestParagraphBordersHtmlRoundTrip:
    def test_borders_render_in_html(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("bordered")
        para.set_borders(_box_borders())

        html = doc.to_html()
        assert "data-dw-borders=" in html
        assert "border-top" in html

    def test_borders_survive_html_round_trip(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("bordered")
        para.set_borders(_box_borders(width_pt=1.5))

        html = doc.to_html()
        data = docwow.to_docx(html)
        doc2 = docwow.open(data)
        para2 = doc2.paragraphs[0]
        assert para2.borders is not None
        assert para2.borders.top is not None
        assert abs(para2.borders.top.width_pt - 1.5) < 0.01
