"""Tests for shading being written correctly into OOXML."""

from __future__ import annotations

from lxml import etree

from docwow.models.paragraph import Paragraph
from docwow.models.styles import ParagraphFormatting
from docwow.models.table import Table, TableCell, TableRow
from docwow.models.document import Document
from docwow.writer.document_writer import build_document_xml
from docwow.writer.styles_writer import _write_para_fmt

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _qn(name: str) -> str:
    return f"{{{W}}}{name}"


class TestParagraphShadingWriter:
    def _write(self, shading: str | None) -> etree._Element:
        ppr = etree.Element(_qn("pPr"))
        fmt = ParagraphFormatting(shading=shading)
        _write_para_fmt(ppr, fmt)
        return ppr

    def test_shading_written_as_w_shd(self):
        ppr = self._write("4472C4")
        shd = ppr.find(_qn("shd"))
        assert shd is not None
        assert shd.get(_qn("val")) == "clear"
        assert shd.get(_qn("color")) == "auto"
        assert shd.get(_qn("fill")) == "4472C4"

    def test_no_shading_omits_w_shd(self):
        ppr = self._write(None)
        assert ppr.find(_qn("shd")) is None


class TestTableCellShadingWriter:
    def _build_doc(self, shading: str | None) -> bytes:
        cell = TableCell(paragraphs=(Paragraph(runs=(), formatting=ParagraphFormatting()),), shading=shading)
        row = TableRow(cells=(cell,))
        table = Table(rows=(row,))
        doc = Document(body=(table,), styles=(), numbering=(), page_width_pt=595.28, page_height_pt=841.89, margin_top_pt=72.0, margin_bottom_pt=72.0, margin_left_pt=72.0, margin_right_pt=72.0)
        return build_document_xml(doc, image_rids={})

    def _parse(self, xml_bytes: bytes) -> etree._Element:
        return etree.fromstring(xml_bytes)

    def test_cell_shading_written(self):
        xml = self._build_doc("ED7D31")
        root = self._parse(xml)
        shd = root.find(f".//{_qn('shd')}")
        assert shd is not None
        assert shd.get(_qn("fill")) == "ED7D31"
        assert shd.get(_qn("val")) == "clear"
        assert shd.get(_qn("color")) == "auto"

    def test_no_cell_shading_omits_w_shd(self):
        xml = self._build_doc(None)
        root = self._parse(xml)
        # Only shd that could exist would be from paragraph (there is none)
        shd = root.find(f".//{_qn('shd')}")
        assert shd is None
