"""Tests for TOC parsing in docwow.parser.body_parser."""
from __future__ import annotations

import io
import zipfile

import pytest
from lxml import etree

from docwow.models.toc import TableOfContents, TocEntry
from docwow.parser.body_parser import parse_body

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _empty_zip() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


def _body(inner_xml: str) -> etree._Element:
    return etree.fromstring(f'<w:body xmlns:w="{_W}">{inner_xml}</w:body>')


def _minimal_toc_xml(title: str = "Contents", entries: list[tuple[str, str, int]] | None = None) -> str:
    """Build a minimal w:sdt TOC XML fragment."""
    entry_xml = ""
    for text, anchor, level in (entries or []):
        entry_xml += (
            f'<w:p><w:pPr><w:pStyle w:val="TOC{level}"/></w:pPr>'
            f'<w:hyperlink w:anchor="{anchor}"><w:r><w:t>{text}</w:t></w:r></w:hyperlink></w:p>'
        )
    return (
        '<w:sdt>'
        '<w:sdtPr>'
        '<w:tag w:val="Table of Contents"/>'
        '<w:docPartObj>'
        '<w:docPartGallery w:val="Table of Contents"/>'
        '<w:docPartUnique/>'
        '</w:docPartObj>'
        '</w:sdtPr>'
        '<w:sdtContent>'
        f'<w:p><w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr><w:r><w:t>{title}</w:t></w:r></w:p>'
        f'{entry_xml}'
        '</w:sdtContent>'
        '</w:sdt>'
    )


class TestTocParsed:
    def test_sdt_toc_produces_table_of_contents(self):
        body = _body(_minimal_toc_xml())
        elements = parse_body(body, _empty_zip(), {})
        toc_elements = [e for e in elements if isinstance(e, TableOfContents)]
        assert len(toc_elements) == 1

    def test_toc_title_extracted(self):
        body = _body(_minimal_toc_xml(title="My TOC"))
        elements = parse_body(body, _empty_zip(), {})
        toc = next(e for e in elements if isinstance(e, TableOfContents))
        assert toc.title == "My TOC"

    def test_toc_entries_extracted(self):
        body = _body(_minimal_toc_xml(entries=[
            ("Introduction", "_Toc1", 1),
            ("Background", "_Toc2", 2),
        ]))
        elements = parse_body(body, _empty_zip(), {})
        toc = next(e for e in elements if isinstance(e, TableOfContents))
        assert len(toc.entries) == 2

    def test_entry_text(self):
        body = _body(_minimal_toc_xml(entries=[("Hello World", "_Toc99", 1)]))
        elements = parse_body(body, _empty_zip(), {})
        toc = next(e for e in elements if isinstance(e, TableOfContents))
        assert toc.entries[0].text == "Hello World"

    def test_entry_url(self):
        body = _body(_minimal_toc_xml(entries=[("x", "_TocABC", 1)]))
        elements = parse_body(body, _empty_zip(), {})
        toc = next(e for e in elements if isinstance(e, TableOfContents))
        assert toc.entries[0].url == "#_TocABC"

    def test_entry_level(self):
        body = _body(_minimal_toc_xml(entries=[
            ("A", "_Toc1", 1),
            ("B", "_Toc2", 2),
            ("C", "_Toc3", 3),
        ]))
        elements = parse_body(body, _empty_zip(), {})
        toc = next(e for e in elements if isinstance(e, TableOfContents))
        assert [e.level for e in toc.entries] == [1, 2, 3]

    def test_non_toc_sdt_skipped(self):
        xml = (
            '<w:sdt>'
            '<w:sdtPr><w:tag w:val="SomeOtherTag"/></w:sdtPr>'
            '<w:sdtContent>'
            '<w:p><w:r><w:t>some content</w:t></w:r></w:p>'
            '</w:sdtContent>'
            '</w:sdt>'
        )
        body = _body(xml)
        elements = parse_body(body, _empty_zip(), {})
        assert not any(isinstance(e, TableOfContents) for e in elements)

    def test_toc_detected_by_style_fallback(self):
        """TOC should be detected even without w:tag if paragraphs use TOC styles."""
        xml = (
            '<w:sdt>'
            '<w:sdtPr/>'
            '<w:sdtContent>'
            '<w:p><w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr><w:r><w:t>Contents</w:t></w:r></w:p>'
            '<w:p><w:pPr><w:pStyle w:val="TOC1"/></w:pPr><w:r><w:t>Intro</w:t></w:r></w:p>'
            '</w:sdtContent>'
            '</w:sdt>'
        )
        body = _body(xml)
        elements = parse_body(body, _empty_zip(), {})
        toc_elements = [e for e in elements if isinstance(e, TableOfContents)]
        assert len(toc_elements) == 1

    def test_empty_sdt_content_skipped(self):
        xml = '<w:sdt><w:sdtPr><w:tag w:val="Table of Contents"/></w:sdtPr><w:sdtContent/></w:sdt>'
        body = _body(xml)
        elements = parse_body(body, _empty_zip(), {})
        assert not any(isinstance(e, TableOfContents) for e in elements)


class TestBookmarkSkipRuleUpdated:
    """Verify that _Toc... bookmarks are now preserved (only _GoBack is skipped)."""

    def test_toc_bookmark_preserved(self):
        from docwow.parser.body_parser import _parse_paragraph
        from docwow.models.paragraph import BookmarkStart

        p_el = etree.fromstring(
            f'<w:p xmlns:w="{_W}">'
            '<w:bookmarkStart w:id="0" w:name="_Toc123456789"/>'
            '</w:p>'
        )
        para = _parse_paragraph(p_el, _empty_zip(), {})
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 1
        assert bm_runs[0].name == "_Toc123456789"

    def test_goback_bookmark_still_skipped(self):
        from docwow.parser.body_parser import _parse_paragraph
        from docwow.models.paragraph import BookmarkStart

        p_el = etree.fromstring(
            f'<w:p xmlns:w="{_W}">'
            '<w:bookmarkStart w:id="0" w:name="_GoBack"/>'
            '</w:p>'
        )
        para = _parse_paragraph(p_el, _empty_zip(), {})
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 0
