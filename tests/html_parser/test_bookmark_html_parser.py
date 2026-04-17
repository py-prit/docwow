"""Tests for bookmark parsing in docwow.html_parser.paragraph_parser."""
from __future__ import annotations

import lxml.html
import pytest

from docwow.html_parser.paragraph_parser import parse_paragraph
from docwow.models.paragraph import BookmarkStart, TextRun


def _el(html_str: str):
    return lxml.html.fragment_fromstring(html_str)


def _p(inner: str = "", extra_attrs: str = "") -> object:
    return _el(f'<p class="dw-p" {extra_attrs}>{inner}</p>')


class TestBookmarkHTMLParsing:
    def test_bookmark_anchor_produces_bookmark_start(self):
        p = _p('<a id="intro" class="dw-bookmark" data-dw-bookmark="intro"></a>')
        para = parse_paragraph(p)
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 1

    def test_bookmark_name_extracted_from_data_attribute(self):
        p = _p('<a id="sec1" class="dw-bookmark" data-dw-bookmark="sec1"></a>')
        para = parse_paragraph(p)
        bm = next(r for r in para.runs if isinstance(r, BookmarkStart))
        assert bm.name == "sec1"

    def test_bookmark_before_text_run(self):
        p = _p(
            '<a id="anchor" class="dw-bookmark" data-dw-bookmark="anchor"></a>'
            '<span class="dw-r">Hello</span>'
        )
        para = parse_paragraph(p)
        assert isinstance(para.runs[0], BookmarkStart)
        assert isinstance(para.runs[1], TextRun)
        assert para.runs[1].text == "Hello"

    def test_bookmark_after_text_run(self):
        p = _p(
            '<span class="dw-r">Hello</span>'
            '<a id="end" class="dw-bookmark" data-dw-bookmark="end"></a>'
        )
        para = parse_paragraph(p)
        assert isinstance(para.runs[0], TextRun)
        assert isinstance(para.runs[1], BookmarkStart)
        assert para.runs[1].name == "end"

    def test_multiple_bookmarks(self):
        p = _p(
            '<a id="first" class="dw-bookmark" data-dw-bookmark="first"></a>'
            '<span class="dw-r">text</span>'
            '<a id="second" class="dw-bookmark" data-dw-bookmark="second"></a>'
        )
        para = parse_paragraph(p)
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 2
        assert bm_runs[0].name == "first"
        assert bm_runs[1].name == "second"

    def test_hyperlink_anchor_not_confused_with_bookmark(self):
        # A hyperlink anchor has data-dw-href, not data-dw-bookmark
        p = _p('<a href="#section" data-dw-href="#section" class="dw-hyperlink">'
               '<span class="dw-r">link</span></a>')
        para = parse_paragraph(p)
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 0
