"""Tests for TOC writing in docwow.writer.document_writer."""
from __future__ import annotations

import pytest
from lxml import etree

from docwow.models.document import Document
from docwow.models.toc import TableOfContents, TocEntry
from docwow.writer.document_writer import build_document_xml

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _doc(body=()):
    return Document(
        body=body,
        styles=(),
        numbering=(),
        page_width_pt=595.28,
        page_height_pt=841.89,
        margin_top_pt=72.0,
        margin_bottom_pt=72.0,
        margin_left_pt=72.0,
        margin_right_pt=72.0,
    )


def _toc(title: str = "Contents", entries: list[tuple[str, str, int]] | None = None) -> TableOfContents:
    return TableOfContents(
        title=title,
        entries=tuple(TocEntry(text=t, url=u, level=l) for t, u, l in (entries or [])),
    )


def _xml(doc) -> str:
    return build_document_xml(doc, {}).decode("utf-8")


def _root(doc) -> etree._Element:
    return etree.fromstring(build_document_xml(doc, {}))


def _ns(tag: str) -> str:
    return f"{{{_W}}}{tag}"


class TestTocWritten:
    def test_sdt_element_present(self):
        xml = _xml(_doc(body=(_toc(),)))
        assert "sdt" in xml

    def test_sdt_pr_tag_attribute(self):
        xml = _xml(_doc(body=(_toc(),)))
        assert 'w:val="Table of Contents"' in xml

    def test_doc_part_gallery_attribute(self):
        xml = _xml(_doc(body=(_toc(),)))
        assert "Table of Contents" in xml

    def test_toc_heading_paragraph(self):
        xml = _xml(_doc(body=(_toc("My Heading"),)))
        assert "TOCHeading" in xml
        assert "My Heading" in xml

    def test_toc_entry_paragraph_style(self):
        xml = _xml(_doc(body=(_toc(entries=[("Intro", "#_Toc1", 1)]),)))
        assert 'w:val="TOC1"' in xml

    def test_toc_entry_text(self):
        xml = _xml(_doc(body=(_toc(entries=[("Introduction", "#_Toc1", 1)]),)))
        assert "Introduction" in xml

    def test_toc_entry_hyperlink_anchor(self):
        xml = _xml(_doc(body=(_toc(entries=[("Intro", "#_Toc1", 1)]),)))
        assert 'w:anchor="_Toc1"' in xml

    def test_toc_entry_level_2(self):
        xml = _xml(_doc(body=(_toc(entries=[("Sec 1.1", "#_Toc2", 2)]),)))
        assert 'w:val="TOC2"' in xml

    def test_multiple_entries_written(self):
        toc = _toc(entries=[
            ("Chapter 1", "#_Toc1", 1),
            ("Section 1.1", "#_Toc2", 2),
        ])
        xml = _xml(_doc(body=(toc,)))
        assert "Chapter 1" in xml
        assert "Section 1.1" in xml

    def test_entry_without_url_written_as_plain_run(self):
        xml = _xml(_doc(body=(_toc(entries=[("No Link", "", 1)]),)))
        assert "No Link" in xml

    def test_sdt_content_element_present(self):
        root = _root(_doc(body=(_toc(),)))
        ns = {"w": _W}
        sdt_content = root.findall(".//w:sdtContent", ns)
        assert len(sdt_content) >= 1
