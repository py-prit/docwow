"""Round-trip integration tests for character styles."""

from __future__ import annotations

from pathlib import Path

import docwow
from docwow.models.document import Document
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
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


class TestCharStyleRoundTrip:
    def test_char_style_survives_round_trip(self):
        run = TextRun(text="Strong text", formatting=RunFormatting(char_style_id="Strong"))
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        doc = _doc(para)
        final = _round_trip(doc)
        assert final.body[0].runs[0].formatting.char_style_id == "Strong"

    def test_no_char_style_survives_round_trip(self):
        run = TextRun(text="Plain", formatting=RunFormatting())
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        doc = _doc(para)
        final = _round_trip(doc)
        assert final.body[0].runs[0].formatting.char_style_id is None

    def test_multiple_styles_in_one_paragraph(self):
        runs = (
            TextRun(text="Plain ", formatting=RunFormatting()),
            TextRun(text="Strong", formatting=RunFormatting(char_style_id="Strong")),
            TextRun(text=" Emphasis", formatting=RunFormatting(char_style_id="Emphasis")),
        )
        para = Paragraph(runs=runs, formatting=ParagraphFormatting())
        doc = _doc(para)
        final = _round_trip(doc)
        assert final.body[0].runs[0].formatting.char_style_id is None
        assert final.body[0].runs[1].formatting.char_style_id == "Strong"
        assert final.body[0].runs[2].formatting.char_style_id == "Emphasis"


class TestCharStyleFixtureRoundTrip:
    def test_char_styles_docx_fixture_round_trip(self):
        data = (FIXTURES / "char_styles.docx").read_bytes()
        doc = parse_docx(data)

        para = doc.body[0]
        assert para.runs[1].formatting.char_style_id == "Strong"
        assert para.runs[3].formatting.char_style_id == "Emphasis"

        html = render_html(doc)
        rt_doc = parse_html(html)
        docx_bytes = write_docx(rt_doc)
        final = parse_docx(docx_bytes)

        assert final.body[0].runs[1].formatting.char_style_id == "Strong"
        assert final.body[0].runs[3].formatting.char_style_id == "Emphasis"


class TestCharStylePublicApi:
    def test_open_exposes_char_style_on_run(self):
        data = (FIXTURES / "char_styles.docx").read_bytes()
        wrapper = docwow.open(data)
        from docwow.api.paragraph import MutableParagraph
        for item in wrapper.paragraphs:
            if isinstance(item, MutableParagraph):
                para = item
                break
        strong_run = para.runs[1]
        assert strong_run.char_style_id == "Strong"

    def test_set_char_style_via_api(self):
        data = (FIXTURES / "char_styles.docx").read_bytes()
        wrapper = docwow.open(data)
        from docwow.api.paragraph import MutableParagraph
        for item in wrapper.paragraphs:
            if isinstance(item, MutableParagraph):
                para = item
                break
        run = para.runs[1]
        run.set_char_style("Emphasis")
        assert run.char_style_id == "Emphasis"
