"""Tests for section break rendering."""

from __future__ import annotations

from docwow.models.section import SectionBreak, SectionProperties
from docwow.renderer.html_renderer import _render_section_break


def _sb(break_type="nextPage", width=595.28, height=841.89,
        top=72.0, bottom=72.0, left=72.0, right=72.0) -> SectionBreak:
    return SectionBreak(properties=SectionProperties(
        page_width_pt=width, page_height_pt=height,
        margin_top_pt=top, margin_bottom_pt=bottom,
        margin_left_pt=left, margin_right_pt=right,
        break_type=break_type,
    ))


class TestSectionBreakRenderer:
    def test_renders_as_div(self):
        html = _render_section_break(_sb())
        assert html.startswith("<div ")
        assert html.endswith("></div>")

    def test_has_dw_section_break_class(self):
        assert 'class="dw-section-break"' in _render_section_break(_sb())

    def test_break_type_attr(self):
        html = _render_section_break(_sb(break_type="continuous"))
        assert 'data-dw-break-type="continuous"' in html

    def test_page_width_attr(self):
        html = _render_section_break(_sb(width=612.0))
        assert 'data-dw-page-width="612pt"' in html

    def test_page_height_attr(self):
        html = _render_section_break(_sb(height=792.0))
        assert 'data-dw-page-height="792pt"' in html

    def test_margins_in_attrs(self):
        html = _render_section_break(_sb(top=36.0, left=54.0))
        assert 'data-dw-margin-top="36pt"' in html
        assert 'data-dw-margin-left="54pt"' in html
