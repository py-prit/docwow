"""Tests for parsing character style data-attributes from HTML."""

from __future__ import annotations

from lxml import etree

from docwow.html_parser.paragraph_parser import parse_paragraph


class TestCharStyleHtmlParser:
    def _make_p(self, char_style_id: str | None) -> etree._Element:
        p = etree.Element("p")
        p.set("class", "dw-p")
        span = etree.SubElement(p, "span")
        span.set("class", "dw-r")
        if char_style_id:
            span.set("data-dw-char-style", char_style_id)
        span.text = "hello"
        return p

    def test_char_style_parsed(self):
        p = self._make_p("Strong")
        para = parse_paragraph(p)
        assert para.runs[0].formatting.char_style_id == "Strong"

    def test_no_char_style_gives_none(self):
        p = self._make_p(None)
        para = parse_paragraph(p)
        assert para.runs[0].formatting.char_style_id is None
