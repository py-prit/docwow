"""Tests for header_footer_writer."""
from __future__ import annotations

from lxml import etree

from docwow.models.header_footer import HeaderFooter
from docwow.models.paragraph import PageNumberField, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.writer.header_footer_writer import build_footer_xml, build_header_xml


def _para(text: str) -> Paragraph:
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(),
    )


class TestBuildHeaderXml:
    def test_produces_bytes(self):
        hf = HeaderFooter(paragraphs=(_para("Hello"),))
        result = build_header_xml(hf, {}, {})
        assert isinstance(result, bytes)

    def test_root_tag_is_hdr(self):
        hf = HeaderFooter(paragraphs=(_para("Hello"),))
        result = build_header_xml(hf, {}, {})
        root = etree.fromstring(result)
        assert root.tag.endswith("}hdr")

    def test_paragraph_text_present(self):
        hf = HeaderFooter(paragraphs=(_para("My Header"),))
        result = build_header_xml(hf, {}, {})
        assert b"My Header" in result

    def test_empty_hf_gets_fallback_paragraph(self):
        hf = HeaderFooter(paragraphs=())
        result = build_header_xml(hf, {}, {})
        root = etree.fromstring(result)
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        paras = root.findall(f"{{{W}}}p")
        assert len(paras) == 1


class TestBuildFooterXml:
    def test_produces_bytes(self):
        hf = HeaderFooter(paragraphs=(_para("Footer"),))
        result = build_footer_xml(hf, {}, {})
        assert isinstance(result, bytes)

    def test_root_tag_is_ftr(self):
        hf = HeaderFooter(paragraphs=(_para("Footer"),))
        result = build_footer_xml(hf, {}, {})
        root = etree.fromstring(result)
        assert root.tag.endswith("}ftr")

    def test_page_number_field_written(self):
        hf = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(TextRun(text="Page "), PageNumberField(field_type="PAGE")),
                formatting=ParagraphFormatting(),
            ),
        ))
        result = build_footer_xml(hf, {}, {})
        # PAGE field instruction must appear somewhere in the XML
        assert b"PAGE" in result

    def test_numpages_field_written(self):
        hf = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(PageNumberField(field_type="NUMPAGES"),),
                formatting=ParagraphFormatting(),
            ),
        ))
        result = build_footer_xml(hf, {}, {})
        assert b"NUMPAGES" in result
