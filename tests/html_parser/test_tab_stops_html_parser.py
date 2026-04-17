"""Tests for parsing tab stops and tab characters from HTML."""

from __future__ import annotations

import lxml.html

from docwow.html_parser.paragraph_parser import parse_paragraph, _parse_tab_stops
from docwow.models.styles import TabStop


def _p(attrs: str = "", inner: str = "") -> object:
    return lxml.html.fragment_fromstring(f'<p class="dw-p" {attrs}>{inner}</p>')


class TestParseTabStops:
    def test_empty_string_returns_empty(self):
        assert _parse_tab_stops("") == ()

    def test_none_returns_empty(self):
        assert _parse_tab_stops(None) == ()

    def test_single_left(self):
        stops = _parse_tab_stops("36pt:left")
        assert len(stops) == 1
        assert stops[0].position_pt == 36.0
        assert stops[0].alignment == "left"
        assert stops[0].leader is None

    def test_with_leader(self):
        stops = _parse_tab_stops("72pt:right:dot")
        assert stops[0].leader == "dot"

    def test_multiple(self):
        stops = _parse_tab_stops("36pt:left,144pt:center:hyphen")
        assert len(stops) == 2
        assert stops[1].alignment == "center"
        assert stops[1].leader == "hyphen"


class TestParagraphTabStopsHtmlParser:
    def test_tab_stops_parsed(self):
        para = parse_paragraph(_p('data-dw-tab-stops="36pt:left,72pt:right:dot"'))
        assert len(para.formatting.tab_stops) == 2
        assert para.formatting.tab_stops[0].position_pt == 36.0
        assert para.formatting.tab_stops[1].leader == "dot"

    def test_no_tab_stops_attr_gives_empty(self):
        para = parse_paragraph(_p())
        assert para.formatting.tab_stops == ()
