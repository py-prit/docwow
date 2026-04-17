"""Tests for multiple section parsing (w:sectPr in w:pPr)."""

from __future__ import annotations

import zipfile
import io

from lxml import etree

from docwow.models.section import SectionBreak, SectionProperties
from docwow.parser.body_parser import parse_body
from docwow.parser.docx_parser import parse_sect_pr
from docwow.utils.xml_utils import qn

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _empty_zf() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


def _body_xml(inner: str) -> etree._Element:
    return etree.fromstring(f'<w:body xmlns:w="{W}">{inner}</w:body>')


def _sect_pr(
    width: int = 12240, height: int = 15840,
    top: int = 1440, bottom: int = 1440, left: int = 1440, right: int = 1440,
    break_type: str | None = None,
) -> str:
    type_xml = f'<w:type w:val="{break_type}"/>' if break_type else ""
    return (
        f'<w:sectPr>'
        f'{type_xml}'
        f'<w:pgSz w:w="{width}" w:h="{height}"/>'
        f'<w:pgMar w:top="{top}" w:right="{right}" w:bottom="{bottom}" w:left="{left}"/>'
        f'</w:sectPr>'
    )


class TestParseSectPr:
    def test_page_size(self):
        xml = etree.fromstring(f'<w:sectPr xmlns:w="{W}"><w:pgSz w:w="12240" w:h="15840"/></w:sectPr>')
        props = parse_sect_pr(xml)
        assert props.page_width_pt == pytest.approx(612.0)
        assert props.page_height_pt == pytest.approx(792.0)

    def test_margins(self):
        xml = etree.fromstring(
            f'<w:sectPr xmlns:w="{W}">'
            f'<w:pgMar w:top="720" w:right="1440" w:bottom="720" w:left="1440"/>'
            f'</w:sectPr>'
        )
        props = parse_sect_pr(xml)
        assert props.margin_top_pt == pytest.approx(36.0)
        assert props.margin_right_pt == pytest.approx(72.0)

    def test_break_type(self):
        xml = etree.fromstring(
            f'<w:sectPr xmlns:w="{W}"><w:type w:val="continuous"/></w:sectPr>'
        )
        props = parse_sect_pr(xml)
        assert props.break_type == "continuous"

    def test_default_break_type(self):
        xml = etree.fromstring(f'<w:sectPr xmlns:w="{W}"></w:sectPr>')
        props = parse_sect_pr(xml)
        assert props.break_type == "nextPage"


import pytest


class TestSectionBreakParser:
    def test_section_break_paragraph_detected(self):
        body = _body_xml(
            f'<w:p><w:r><w:t>Section 1</w:t></w:r></w:p>'
            f'<w:p><w:pPr>{_sect_pr()}</w:pPr></w:p>'
            f'<w:p><w:r><w:t>Section 2</w:t></w:r></w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        section_breaks = [e for e in elements if isinstance(e, SectionBreak)]
        assert len(section_breaks) == 1

    def test_section_break_properties(self):
        body = _body_xml(
            f'<w:p><w:pPr>{_sect_pr(width=15840, height=12240, break_type="continuous")}</w:pPr></w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        sb = next(e for e in elements if isinstance(e, SectionBreak))
        assert sb.properties.page_width_pt == pytest.approx(792.0)
        assert sb.properties.page_height_pt == pytest.approx(612.0)
        assert sb.properties.break_type == "continuous"

    def test_section_break_inserted_after_paragraph(self):
        body = _body_xml(
            f'<w:p><w:r><w:t>Last para of section 1</w:t></w:r>'
            f'<w:pPr>{_sect_pr()}</w:pPr></w:p>'
            f'<w:p><w:r><w:t>Section 2</w:t></w:r></w:p>'
        )
        from docwow.models.paragraph import Paragraph
        elements = parse_body(body, _empty_zf(), {})
        types = [type(e).__name__ for e in elements]
        # Paragraph comes before SectionBreak
        para_idx = next(i for i, t in enumerate(types) if t == "Paragraph")
        sb_idx = next(i for i, t in enumerate(types) if t == "SectionBreak")
        assert para_idx < sb_idx

    def test_no_section_break_without_ppr_sectpr(self):
        body = _body_xml('<w:p><w:r><w:t>plain</w:t></w:r></w:p>')
        elements = parse_body(body, _empty_zf(), {})
        assert not any(isinstance(e, SectionBreak) for e in elements)

    def test_multiple_section_breaks(self):
        body = _body_xml(
            f'<w:p><w:pPr>{_sect_pr()}</w:pPr></w:p>'
            f'<w:p><w:r><w:t>middle</w:t></w:r></w:p>'
            f'<w:p><w:pPr>{_sect_pr(break_type="continuous")}</w:pPr></w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        section_breaks = [e for e in elements if isinstance(e, SectionBreak)]
        assert len(section_breaks) == 2
        assert section_breaks[1].properties.break_type == "continuous"
