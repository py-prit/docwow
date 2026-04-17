"""Tests for tab stop rendering."""

from __future__ import annotations

from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting, TabStop
from docwow.renderer.paragraph_renderer import render_paragraph, _serialize_tab_stops


def _para(tab_stops=(), text="Hello"):
    run = TextRun(text=text, formatting=RunFormatting())
    return Paragraph(runs=(run,), formatting=ParagraphFormatting(tab_stops=tab_stops))


class TestTabStopsDataAttr:
    def test_no_tab_stops_omits_attr(self):
        html = render_paragraph(_para())
        assert "data-dw-tab-stops" not in html

    def test_single_left_stop(self):
        stops = (TabStop(position_pt=36.0, alignment="left"),)
        html = render_paragraph(_para(tab_stops=stops))
        assert 'data-dw-tab-stops="36pt:left"' in html

    def test_stop_with_leader(self):
        stops = (TabStop(position_pt=72.0, alignment="right", leader="dot"),)
        html = render_paragraph(_para(tab_stops=stops))
        assert 'data-dw-tab-stops="72pt:right:dot"' in html

    def test_multiple_stops(self):
        stops = (
            TabStop(position_pt=36.0, alignment="left"),
            TabStop(position_pt=144.0, alignment="center"),
        )
        html = render_paragraph(_para(tab_stops=stops))
        assert 'data-dw-tab-stops="36pt:left,144pt:center"' in html


class TestSerializeTabStops:
    def test_left_no_leader(self):
        assert _serialize_tab_stops((TabStop(36.0, "left"),)) == "36pt:left"

    def test_right_dot_leader(self):
        assert _serialize_tab_stops((TabStop(72.0, "right", "dot"),)) == "72pt:right:dot"

    def test_multiple(self):
        stops = (TabStop(36.0, "left"), TabStop(144.0, "center", "hyphen"))
        assert _serialize_tab_stops(stops) == "36pt:left,144pt:center:hyphen"

    def test_none_leader_not_included(self):
        result = _serialize_tab_stops((TabStop(36.0, "left", None),))
        assert result == "36pt:left"


class TestTabCharacterRendering:
    def test_tab_in_text_preserved(self):
        run = TextRun(text="\t", formatting=RunFormatting())
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        html = render_paragraph(para)
        assert "\t" in html
