"""Tests for parsing data-dw-small-caps and data-dw-all-caps from HTML."""

from __future__ import annotations

import lxml.html

from docwow.html_parser.paragraph_parser import parse_paragraph


def _p(span_attrs: str = "") -> object:
    html = f'<p class="dw-p"><span class="dw-r" {span_attrs}>text</span></p>'
    return lxml.html.fragment_fromstring(html)


class TestSmallCapsHtmlParser:
    def test_small_caps_true(self):
        para = parse_paragraph(_p('data-dw-small-caps="true"'))
        from docwow.models.paragraph import TextRun
        run = para.runs[0]
        assert isinstance(run, TextRun)
        assert run.formatting.small_caps is True

    def test_small_caps_absent_is_false(self):
        para = parse_paragraph(_p())
        from docwow.models.paragraph import TextRun
        run = para.runs[0]
        assert isinstance(run, TextRun)
        assert run.formatting.small_caps is False


class TestAllCapsHtmlParser:
    def test_all_caps_true(self):
        para = parse_paragraph(_p('data-dw-all-caps="true"'))
        from docwow.models.paragraph import TextRun
        run = para.runs[0]
        assert isinstance(run, TextRun)
        assert run.formatting.all_caps is True

    def test_all_caps_absent_is_false(self):
        para = parse_paragraph(_p())
        from docwow.models.paragraph import TextRun
        run = para.runs[0]
        assert isinstance(run, TextRun)
        assert run.formatting.all_caps is False
