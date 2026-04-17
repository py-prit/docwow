"""Tests for parsing section breaks from HTML."""

from __future__ import annotations

import lxml.html

from docwow.html_parser.html_parser import _parse_section_break
from docwow.models.section import SectionBreak


def _div(attrs: str = "") -> object:
    return lxml.html.fragment_fromstring(f'<div class="dw-section-break" {attrs}></div>')


class TestParseSectionBreak:
    def test_returns_section_break(self):
        sb = _parse_section_break(_div())
        assert isinstance(sb, SectionBreak)

    def test_break_type_parsed(self):
        sb = _parse_section_break(_div('data-dw-break-type="continuous"'))
        assert sb.properties.break_type == "continuous"

    def test_default_break_type(self):
        sb = _parse_section_break(_div())
        assert sb.properties.break_type == "nextPage"

    def test_page_dimensions_parsed(self):
        sb = _parse_section_break(_div(
            'data-dw-page-width="612pt" data-dw-page-height="792pt"'
        ))
        assert sb.properties.page_width_pt == 612.0
        assert sb.properties.page_height_pt == 792.0

    def test_margins_parsed(self):
        sb = _parse_section_break(_div(
            'data-dw-margin-top="36pt" data-dw-margin-left="54pt"'
        ))
        assert sb.properties.margin_top_pt == 36.0
        assert sb.properties.margin_left_pt == 54.0

    def test_defaults_when_attrs_absent(self):
        sb = _parse_section_break(_div())
        assert sb.properties.page_width_pt == 595.28
        assert sb.properties.margin_top_pt == 72.0
