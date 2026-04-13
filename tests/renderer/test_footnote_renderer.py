"""Tests for docwow.renderer.footnote_renderer."""
import pytest

from docwow.models.footnote import Footnote
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.renderer.footnote_renderer import render_endnotes, render_footnotes


def _para(text: str) -> Paragraph:
    return Paragraph(runs=(TextRun(text=text),), formatting=ParagraphFormatting())


def _note(note_id: int, text: str, note_type: str = "footnote") -> Footnote:
    return Footnote(
        note_id=note_id,
        paragraphs=(_para(text),),
        note_type=note_type,
    )


class TestRenderFootnotes:
    def test_empty_returns_empty_string(self):
        assert render_footnotes(()) == ""

    def test_section_class(self):
        html = render_footnotes((_note(1, "text"),))
        assert 'class="dw-footnotes"' in html

    def test_data_attr(self):
        html = render_footnotes((_note(1, "text"),))
        assert 'data-dw-note-section="footnotes"' in html

    def test_section_tag(self):
        html = render_footnotes((_note(1, "text"),))
        assert "<section" in html
        assert "</section>" in html

    def test_item_id_anchor(self):
        html = render_footnotes((_note(1, "text"),))
        assert 'id="fn-1"' in html

    def test_item_class(self):
        html = render_footnotes((_note(1, "text"),))
        assert 'class="dw-fn"' in html

    def test_data_note_id(self):
        html = render_footnotes((_note(1, "text"),))
        assert 'data-dw-note-id="1"' in html

    def test_data_note_type(self):
        html = render_footnotes((_note(1, "text"),))
        assert 'data-dw-note-type="footnote"' in html

    def test_marker_span(self):
        html = render_footnotes((_note(1, "text"),))
        assert 'class="dw-fn-marker"' in html
        assert "[1]" in html

    def test_body_div(self):
        html = render_footnotes((_note(1, "Hello note"),))
        assert 'class="dw-fn-body"' in html
        assert "Hello note" in html

    def test_multiple_footnotes(self):
        html = render_footnotes((_note(1, "first"), _note(2, "second")))
        assert 'id="fn-1"' in html
        assert 'id="fn-2"' in html
        assert "[1]" in html
        assert "[2]" in html


class TestRenderEndnotes:
    def test_empty_returns_empty_string(self):
        assert render_endnotes(()) == ""

    def test_section_class(self):
        html = render_endnotes((_note(1, "text", "endnote"),))
        assert 'class="dw-endnotes"' in html

    def test_data_attr(self):
        html = render_endnotes((_note(1, "text", "endnote"),))
        assert 'data-dw-note-section="endnotes"' in html

    def test_item_id_anchor(self):
        html = render_endnotes((_note(1, "text", "endnote"),))
        assert 'id="en-1"' in html

    def test_item_class(self):
        html = render_endnotes((_note(1, "text", "endnote"),))
        assert 'class="dw-en"' in html

    def test_data_note_type(self):
        html = render_endnotes((_note(1, "text", "endnote"),))
        assert 'data-dw-note-type="endnote"' in html

    def test_marker_span(self):
        html = render_endnotes((_note(1, "text", "endnote"),))
        assert 'class="dw-en-marker"' in html
        assert "[1]" in html
