"""Tests for parsing cross-reference links from HTML."""

from __future__ import annotations

import lxml.html

from docwow.html_parser.paragraph_parser import parse_paragraph
from docwow.models.paragraph import CrossRef


def _p(inner: str = "") -> object:
    return lxml.html.fragment_fromstring(f'<p class="dw-p">{inner}</p>')


class TestCrossRefHtmlParser:
    def test_dw_xref_parsed_as_cross_ref(self):
        para = parse_paragraph(_p(
            '<a class="dw-xref" href="#MyBookmark" data-dw-xref="MyBookmark">Section 1</a>'
        ))
        assert len(para.runs) == 1
        ref = para.runs[0]
        assert isinstance(ref, CrossRef)
        assert ref.bookmark_name == "MyBookmark"

    def test_display_text_captured(self):
        para = parse_paragraph(_p(
            '<a class="dw-xref" href="#Ref123" data-dw-xref="Ref123">Chapter 2</a>'
        ))
        ref = para.runs[0]
        assert isinstance(ref, CrossRef)
        assert ref.display_text == "Chapter 2"

    def test_missing_data_dw_xref_not_parsed_as_cross_ref(self):
        para = parse_paragraph(_p('<a href="#foo">plain link</a>'))
        assert not any(isinstance(r, CrossRef) for r in para.runs)
