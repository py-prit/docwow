"""Tests for tab stop and tab character writing."""

from __future__ import annotations

import zipfile
import io

from lxml import etree

from docwow.models.styles import ParagraphFormatting, TabStop
from docwow.writer.styles_writer import _write_para_fmt
from docwow.writer.document_writer import _write_text_content

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _qn(name: str) -> str:
    return f"{{{W}}}{name}"


def _ppr(fmt: ParagraphFormatting) -> etree._Element:
    ppr = etree.Element(_qn("pPr"))
    _write_para_fmt(ppr, fmt)
    return ppr


def _run_el() -> etree._Element:
    return etree.Element(_qn("r"))


class TestTabStopsWriter:
    def test_single_left_stop_written(self):
        stops = (TabStop(position_pt=36.0, alignment="left"),)
        ppr = _ppr(ParagraphFormatting(tab_stops=stops))
        tabs = ppr.find(_qn("tabs"))
        assert tabs is not None
        tab_els = tabs.findall(_qn("tab"))
        assert len(tab_els) == 1
        assert tab_els[0].get(_qn("val")) == "left"
        assert tab_els[0].get(_qn("pos")) == "720"  # 36pt = 720 twips

    def test_leader_written(self):
        stops = (TabStop(position_pt=72.0, alignment="right", leader="dot"),)
        ppr = _ppr(ParagraphFormatting(tab_stops=stops))
        tab_el = ppr.find(_qn("tabs")).find(_qn("tab"))
        assert tab_el.get(_qn("leader")) == "dot"

    def test_no_leader_omits_attribute(self):
        stops = (TabStop(position_pt=36.0, alignment="left"),)
        ppr = _ppr(ParagraphFormatting(tab_stops=stops))
        tab_el = ppr.find(_qn("tabs")).find(_qn("tab"))
        assert tab_el.get(_qn("leader")) is None

    def test_multiple_stops(self):
        stops = (
            TabStop(36.0, "left"),
            TabStop(144.0, "center"),
            TabStop(288.0, "right"),
        )
        ppr = _ppr(ParagraphFormatting(tab_stops=stops))
        tab_els = ppr.find(_qn("tabs")).findall(_qn("tab"))
        assert len(tab_els) == 3

    def test_no_tab_stops_omits_tabs_element(self):
        ppr = _ppr(ParagraphFormatting())
        assert ppr.find(_qn("tabs")) is None


class TestTabCharacterWriter:
    def test_tab_written_as_w_tab(self):
        r_el = _run_el()
        _write_text_content(r_el, "\t")
        tags = [c.tag for c in r_el]
        assert _qn("tab") in tags

    def test_text_before_tab(self):
        r_el = _run_el()
        _write_text_content(r_el, "before\tafter")
        tags = [c.tag for c in r_el]
        assert tags.count(_qn("tab")) == 1
        assert tags.count(_qn("t")) == 2

    def test_two_tabs(self):
        r_el = _run_el()
        _write_text_content(r_el, "a\tb\tc")
        tags = [c.tag for c in r_el]
        assert tags.count(_qn("tab")) == 2
        assert tags.count(_qn("t")) == 3
