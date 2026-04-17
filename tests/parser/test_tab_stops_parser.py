"""Tests for w:tabs and w:tab parsing."""

from __future__ import annotations

import zipfile
import io

from lxml import etree

from docwow.models.styles import TabStop
from docwow.parser.style_parser import parse_para_fmt
from docwow.parser.body_parser import parse_body
from docwow.models.paragraph import Paragraph, TextRun
from docwow.utils.xml_utils import qn

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _pPr(inner: str = "") -> etree._Element:
    xml = f'<w:pPr xmlns:w="{W}">{inner}</w:pPr>'
    return etree.fromstring(xml)


def _empty_zf() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


def _body_xml(inner: str) -> etree._Element:
    return etree.fromstring(f'<w:body xmlns:w="{W}">{inner}</w:body>')


class TestTabStopsParser:
    def test_single_left_tab_stop(self):
        fmt = parse_para_fmt(_pPr('<w:tabs><w:tab w:val="left" w:pos="720"/></w:tabs>'))
        assert len(fmt.tab_stops) == 1
        assert fmt.tab_stops[0].position_pt == 36.0
        assert fmt.tab_stops[0].alignment == "left"
        assert fmt.tab_stops[0].leader is None

    def test_center_tab_stop(self):
        fmt = parse_para_fmt(_pPr('<w:tabs><w:tab w:val="center" w:pos="1440"/></w:tabs>'))
        assert fmt.tab_stops[0].alignment == "center"
        assert fmt.tab_stops[0].position_pt == 72.0

    def test_right_tab_stop(self):
        fmt = parse_para_fmt(_pPr('<w:tabs><w:tab w:val="right" w:pos="2880"/></w:tabs>'))
        assert fmt.tab_stops[0].alignment == "right"
        assert fmt.tab_stops[0].position_pt == 144.0

    def test_decimal_tab_stop(self):
        fmt = parse_para_fmt(_pPr('<w:tabs><w:tab w:val="decimal" w:pos="1440"/></w:tabs>'))
        assert fmt.tab_stops[0].alignment == "decimal"

    def test_dot_leader(self):
        fmt = parse_para_fmt(_pPr('<w:tabs><w:tab w:val="right" w:pos="1440" w:leader="dot"/></w:tabs>'))
        assert fmt.tab_stops[0].leader == "dot"

    def test_leader_none_omitted(self):
        fmt = parse_para_fmt(_pPr('<w:tabs><w:tab w:val="left" w:pos="720" w:leader="none"/></w:tabs>'))
        assert fmt.tab_stops[0].leader is None

    def test_multiple_tab_stops(self):
        fmt = parse_para_fmt(_pPr(
            '<w:tabs>'
            '<w:tab w:val="left" w:pos="720"/>'
            '<w:tab w:val="center" w:pos="2880"/>'
            '<w:tab w:val="right" w:pos="5760"/>'
            '</w:tabs>'
        ))
        assert len(fmt.tab_stops) == 3
        assert fmt.tab_stops[0].alignment == "left"
        assert fmt.tab_stops[1].alignment == "center"
        assert fmt.tab_stops[2].alignment == "right"

    def test_clear_tab_stops_skipped(self):
        fmt = parse_para_fmt(_pPr('<w:tabs><w:tab w:val="clear" w:pos="720"/></w:tabs>'))
        assert len(fmt.tab_stops) == 0

    def test_no_tabs_element(self):
        fmt = parse_para_fmt(_pPr())
        assert fmt.tab_stops == ()


class TestTabRunParser:
    def test_tab_run_parsed_as_tab_character(self):
        body = _body_xml('<w:p><w:r><w:tab/></w:r></w:p>')
        elements = parse_body(body, _empty_zf(), {})
        para = elements[0]
        assert isinstance(para, Paragraph)
        assert len(para.runs) == 1
        run = para.runs[0]
        assert isinstance(run, TextRun)
        assert run.text == "\t"

    def test_tab_between_text(self):
        body = _body_xml(
            '<w:p>'
            '<w:r><w:t>before</w:t></w:r>'
            '<w:r><w:tab/></w:r>'
            '<w:r><w:t>after</w:t></w:r>'
            '</w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        para = elements[0]
        texts = [r.text for r in para.runs if isinstance(r, TextRun)]
        assert texts == ["before", "\t", "after"]
