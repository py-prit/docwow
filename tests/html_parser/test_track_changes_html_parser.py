"""Tests for track changes HTML parsing."""
from __future__ import annotations

from docwow.models.paragraph import TrackedChange
from docwow.html_parser.paragraph_parser import parse_paragraph
from lxml import etree


def _parse(html: str):
    return parse_paragraph(etree.fromstring(html))


class TestParseInsertionFromHtml:
    def test_basic_ins(self):
        para = _parse(
            '<p class="dw-p">'
            '<ins class="dw-ins" data-dw-author="Alice" data-dw-date="2024-01-15T10:00:00Z" data-dw-change-id="1">'
            '<span class="dw-r">inserted</span>'
            '</ins>'
            '</p>'
        )
        assert len(para.runs) == 1
        tc = para.runs[0]
        assert isinstance(tc, TrackedChange)
        assert tc.change_type == "insert"
        assert tc.author == "Alice"
        assert tc.date == "2024-01-15T10:00:00Z"
        assert tc.change_id == 1
        assert tc.runs[0].text == "inserted"

    def test_ins_without_class_not_parsed(self):
        para = _parse(
            '<p class="dw-p">'
            '<ins data-dw-author="A" data-dw-date="" data-dw-change-id="1">'
            '<span class="dw-r">x</span>'
            '</ins>'
            '</p>'
        )
        # ins without dw-ins class should be ignored
        assert len(para.runs) == 0


class TestParseDeletionFromHtml:
    def test_basic_del(self):
        para = _parse(
            '<p class="dw-p">'
            '<del class="dw-del" data-dw-author="Bob" data-dw-date="2024-02-01T08:00:00Z" data-dw-change-id="5">'
            '<span class="dw-r">deleted</span>'
            '</del>'
            '</p>'
        )
        tc = para.runs[0]
        assert isinstance(tc, TrackedChange)
        assert tc.change_type == "delete"
        assert tc.author == "Bob"
        assert tc.runs[0].text == "deleted"

    def test_del_without_class_not_parsed(self):
        para = _parse(
            '<p class="dw-p">'
            '<del data-dw-author="A" data-dw-date="" data-dw-change-id="1">'
            '<span class="dw-r">x</span>'
            '</del>'
            '</p>'
        )
        assert len(para.runs) == 0


class TestRoundTripFidelity:
    def test_author_preserved(self):
        from docwow.renderer.paragraph_renderer import render_paragraph
        from docwow.models.paragraph import Paragraph, TextRun
        tc = TrackedChange(
            change_type="insert",
            runs=(TextRun(text="hello"),),
            author="Carol",
            date="2024-03-01T12:00:00Z",
            change_id=9,
        )
        html = render_paragraph(Paragraph(runs=(tc,)))
        p_el = etree.fromstring(html)
        restored = parse_paragraph(p_el)
        restored_tc = restored.runs[0]
        assert isinstance(restored_tc, TrackedChange)
        assert restored_tc.change_type == "insert"
        assert restored_tc.author == "Carol"
        assert restored_tc.date == "2024-03-01T12:00:00Z"
        assert restored_tc.change_id == 9
        assert restored_tc.runs[0].text == "hello"
