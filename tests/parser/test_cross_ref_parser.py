"""Tests for REF field (cross-reference) parsing."""

from __future__ import annotations

import zipfile
import io

from lxml import etree

from docwow.models.paragraph import CrossRef, Paragraph, TextRun
from docwow.parser.body_parser import parse_body
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


def _ref_field(bookmark: str, display: str) -> str:
    return (
        f'<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        f'<w:r><w:instrText xml:space="preserve"> REF {bookmark} \\h </w:instrText></w:r>'
        f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        f'<w:r><w:t>{display}</w:t></w:r>'
        f'<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    )


class TestCrossRefParser:
    def test_basic_ref_field(self):
        body = _body_xml(f'<w:p>{_ref_field("_Ref123", "Section 1")}</w:p>')
        elements = parse_body(body, _empty_zf(), {})
        para = elements[0]
        assert isinstance(para, Paragraph)
        assert len(para.runs) == 1
        ref = para.runs[0]
        assert isinstance(ref, CrossRef)
        assert ref.bookmark_name == "_Ref123"
        assert ref.display_text == "Section 1"

    def test_display_text_captured(self):
        body = _body_xml(f'<w:p>{_ref_field("MyBookmark", "Chapter 2")}</w:p>')
        elements = parse_body(body, _empty_zf(), {})
        ref = elements[0].runs[0]
        assert isinstance(ref, CrossRef)
        assert ref.display_text == "Chapter 2"

    def test_ref_with_mixed_content(self):
        xml = (
            '<w:p>'
            '<w:r><w:t xml:space="preserve">See </w:t></w:r>'
            + _ref_field("_Ref456", "Figure 3") +
            '<w:r><w:t xml:space="preserve"> above.</w:t></w:r>'
            '</w:p>'
        )
        body = _body_xml(xml)
        elements = parse_body(body, _empty_zf(), {})
        runs = elements[0].runs
        assert any(isinstance(r, CrossRef) for r in runs)
        ref = next(r for r in runs if isinstance(r, CrossRef))
        assert ref.bookmark_name == "_Ref456"
        assert ref.display_text == "Figure 3"

    def test_page_field_still_works(self):
        body = _body_xml(
            '<w:p>'
            '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:instrText> PAGE </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            '<w:r><w:t>1</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
            '</w:p>'
        )
        from docwow.models.paragraph import PageNumberField
        elements = parse_body(body, _empty_zf(), {})
        pf = elements[0].runs[0]
        assert isinstance(pf, PageNumberField)
        assert pf.field_type == "PAGE"
