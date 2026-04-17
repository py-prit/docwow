"""Tests for parsing shading data-attributes back from HTML."""

from __future__ import annotations

from lxml import etree

from docwow.html_parser.paragraph_parser import parse_paragraph
from docwow.html_parser.table_parser import parse_table


class TestParagraphShadingHtmlParser:
    def _make_p(self, shading: str | None) -> etree._Element:
        p = etree.Element("p")
        p.set("class", "dw-p")
        if shading:
            p.set("data-dw-shading", shading)
        return p

    def test_shading_parsed(self):
        p = self._make_p("4472C4")
        para = parse_paragraph(p)
        assert para.formatting.shading == "4472C4"

    def test_no_shading_gives_none(self):
        p = self._make_p(None)
        para = parse_paragraph(p)
        assert para.formatting.shading is None


class TestTableCellShadingHtmlParser:
    def _make_table(self, shading: str | None) -> etree._Element:
        table = etree.Element("table")
        table.set("class", "dw-table")
        tr = etree.SubElement(table, "tr")
        tr.set("class", "dw-tr")
        td = etree.SubElement(tr, "td")
        td.set("class", "dw-td")
        if shading:
            td.set("data-dw-shading", shading)
        p = etree.SubElement(td, "p")
        p.set("class", "dw-p")
        return table

    def test_cell_shading_parsed(self):
        table_el = self._make_table("ED7D31")
        table = parse_table(table_el)
        assert table.rows[0].cells[0].shading == "ED7D31"

    def test_no_cell_shading_gives_none(self):
        table_el = self._make_table(None)
        table = parse_table(table_el)
        assert table.rows[0].cells[0].shading is None
