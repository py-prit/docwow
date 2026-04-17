"""Tests for section break writing."""

from __future__ import annotations

from lxml import etree

from docwow.models.section import SectionBreak, SectionProperties
from docwow.writer.document_writer import _write_section_break

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _qn(name: str) -> str:
    return f"{{{W}}}{name}"


def _write(props: SectionProperties) -> etree._Element:
    parent = etree.Element(_qn("body"))
    _write_section_break(parent, props)
    return parent


class TestSectionBreakWriter:
    def test_writes_empty_paragraph(self):
        parent = _write(SectionProperties())
        p_el = parent.find(_qn("p"))
        assert p_el is not None

    def test_ppr_contains_sectpr(self):
        parent = _write(SectionProperties())
        p_el = parent.find(_qn("p"))
        pPr = p_el.find(_qn("pPr"))
        assert pPr is not None
        sect_pr = pPr.find(_qn("sectPr"))
        assert sect_pr is not None

    def test_page_size_written(self):
        parent = _write(SectionProperties(page_width_pt=612.0, page_height_pt=792.0))
        sect_pr = parent.find(_qn("p")).find(_qn("pPr")).find(_qn("sectPr"))
        pgSz = sect_pr.find(_qn("pgSz"))
        assert pgSz is not None
        assert pgSz.get(_qn("w")) == "12240"   # 612pt = 12240 twips
        assert pgSz.get(_qn("h")) == "15840"   # 792pt = 15840 twips

    def test_margins_written(self):
        parent = _write(SectionProperties(
            margin_top_pt=36.0, margin_bottom_pt=36.0,
            margin_left_pt=54.0, margin_right_pt=54.0,
        ))
        sect_pr = parent.find(_qn("p")).find(_qn("pPr")).find(_qn("sectPr"))
        pgMar = sect_pr.find(_qn("pgMar"))
        assert pgMar is not None
        assert pgMar.get(_qn("top")) == "720"   # 36pt = 720 twips
        assert pgMar.get(_qn("left")) == "1080" # 54pt = 1080 twips

    def test_break_type_written(self):
        parent = _write(SectionProperties(break_type="continuous"))
        sect_pr = parent.find(_qn("p")).find(_qn("pPr")).find(_qn("sectPr"))
        type_el = sect_pr.find(_qn("type"))
        assert type_el is not None
        assert type_el.get(_qn("val")) == "continuous"
