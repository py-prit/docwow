"""Tests for CrossRef field writing."""

from __future__ import annotations

from lxml import etree

from docwow.models.paragraph import CrossRef
from docwow.writer.document_writer import _write_cross_ref_field

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def _qn(name: str) -> str:
    return f"{{{W}}}{name}"


def _write(bookmark: str, display: str = "") -> list[etree._Element]:
    parent = etree.Element(_qn("p"))
    _write_cross_ref_field(parent, CrossRef(bookmark_name=bookmark, display_text=display))
    return list(parent)


class TestCrossRefWriter:
    def test_emits_five_runs(self):
        runs = _write("MyBookmark", "Section 1")
        assert len(runs) == 5

    def test_begin_fldchar(self):
        runs = _write("Bm", "text")
        fc = runs[0].find(_qn("fldChar"))
        assert fc is not None
        assert fc.get(_qn("fldCharType")) == "begin"

    def test_instr_text_contains_ref(self):
        runs = _write("MyBookmark", "text")
        instr = runs[1].find(_qn("instrText"))
        assert instr is not None
        assert "REF" in instr.text
        assert "MyBookmark" in instr.text

    def test_instr_text_has_hyperlink_switch(self):
        runs = _write("Bm", "text")
        instr = runs[1].find(_qn("instrText"))
        assert "\\h" in instr.text

    def test_separate_fldchar(self):
        runs = _write("Bm", "text")
        fc = runs[2].find(_qn("fldChar"))
        assert fc.get(_qn("fldCharType")) == "separate"

    def test_display_text_written(self):
        runs = _write("Bm", "Chapter 2")
        t_el = runs[3].find(_qn("t"))
        assert t_el is not None
        assert t_el.text == "Chapter 2"

    def test_end_fldchar(self):
        runs = _write("Bm", "text")
        fc = runs[4].find(_qn("fldChar"))
        assert fc.get(_qn("fldCharType")) == "end"

    def test_fallback_to_bookmark_name_when_no_display(self):
        runs = _write("MyBm", "")
        t_el = runs[3].find(_qn("t"))
        assert t_el.text == "MyBm"
