"""Tests for character style being written into OOXML."""

from __future__ import annotations

from lxml import etree

from docwow.models.styles import RunFormatting
from docwow.writer.styles_writer import _write_run_fmt

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _qn(name: str) -> str:
    return f"{{{W}}}{name}"


class TestCharStyleWriter:
    def _write(self, char_style_id: str | None) -> etree._Element:
        rpr = etree.Element(_qn("rPr"))
        fmt = RunFormatting(char_style_id=char_style_id)
        _write_run_fmt(rpr, fmt)
        return rpr

    def test_char_style_written_as_w_rstyle(self):
        rpr = self._write("Strong")
        rstyle = rpr.find(_qn("rStyle"))
        assert rstyle is not None
        assert rstyle.get(_qn("val")) == "Strong"

    def test_no_char_style_omits_w_rstyle(self):
        rpr = self._write(None)
        assert rpr.find(_qn("rStyle")) is None

    def test_rstyle_is_first_child(self):
        """w:rStyle must be the first child of w:rPr per OOXML schema."""
        rpr = etree.Element(_qn("rPr"))
        fmt = RunFormatting(char_style_id="Strong", bold=True, italic=True)
        _write_run_fmt(rpr, fmt)
        assert rpr[0].tag == _qn("rStyle")
