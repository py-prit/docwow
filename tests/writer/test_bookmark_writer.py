"""Tests for bookmark writing in docwow.writer.document_writer."""
from __future__ import annotations

import pytest
from lxml import etree

from docwow.models.document import Document
from docwow.models.paragraph import BookmarkStart, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
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


def _bm_para(name: str, text: str = "Hello"):
    return Paragraph(
        runs=(BookmarkStart(name=name), TextRun(text=text)),
        formatting=ParagraphFormatting(),
    )


def _xml(doc) -> str:
    return build_document_xml(doc, {}).decode("utf-8")


def _root(doc) -> etree._Element:
    return etree.fromstring(build_document_xml(doc, {}))


def _ns(tag: str) -> str:
    return f"{{{_W}}}{tag}"


class TestBookmarkStartWritten:
    def test_bookmark_start_element_present(self):
        xml = _xml(_doc(body=(_bm_para("intro"),)))
        assert "bookmarkStart" in xml

    def test_bookmark_end_element_present(self):
        xml = _xml(_doc(body=(_bm_para("intro"),)))
        assert "bookmarkEnd" in xml

    def test_bookmark_name_attribute(self):
        xml = _xml(_doc(body=(_bm_para("mySection"),)))
        assert 'w:name="mySection"' in xml

    def test_bookmark_id_attribute(self):
        xml = _xml(_doc(body=(_bm_para("intro"),)))
        assert 'w:id="0"' in xml

    def test_bookmark_start_and_end_share_id(self):
        root = _root(_doc(body=(_bm_para("intro"),)))
        ns = {"w": _W}
        starts = root.findall(".//w:bookmarkStart", ns)
        ends = root.findall(".//w:bookmarkEnd", ns)
        assert len(starts) == 1
        assert len(ends) == 1
        assert starts[0].get(_ns("id")) == ends[0].get(_ns("id"))

    def test_multiple_bookmarks_get_unique_ids(self):
        para1 = Paragraph(
            runs=(BookmarkStart(name="first"),),
            formatting=ParagraphFormatting(),
        )
        para2 = Paragraph(
            runs=(BookmarkStart(name="second"),),
            formatting=ParagraphFormatting(),
        )
        root = _root(_doc(body=(para1, para2)))
        ns = {"w": _W}
        starts = root.findall(".//w:bookmarkStart", ns)
        assert len(starts) == 2
        ids = [s.get(_ns("id")) for s in starts]
        assert len(set(ids)) == 2  # each bookmark gets a distinct ID

    def test_bookmark_id_counter_increments(self):
        para1 = Paragraph(
            runs=(BookmarkStart(name="a"),),
            formatting=ParagraphFormatting(),
        )
        para2 = Paragraph(
            runs=(BookmarkStart(name="b"),),
            formatting=ParagraphFormatting(),
        )
        root = _root(_doc(body=(para1, para2)))
        ns = {"w": _W}
        starts = root.findall(".//w:bookmarkStart", ns)
        ids = sorted(int(s.get(_ns("id"))) for s in starts)
        assert ids == [0, 1]

    def test_text_run_still_present_with_bookmark(self):
        xml = _xml(_doc(body=(_bm_para("intro", text="Section One"),)))
        assert "Section One" in xml

    def test_bookmark_only_paragraph(self):
        para = Paragraph(
            runs=(BookmarkStart(name="anchor"),),
            formatting=ParagraphFormatting(),
        )
        xml = _xml(_doc(body=(para,)))
        assert "bookmarkStart" in xml
        assert "bookmarkEnd" in xml


class TestBookmarkInTable:
    def test_bookmark_in_table_cell_written(self):
        from docwow.models.table import Table, TableCell, TableRow
        cell = TableCell(
            paragraphs=(Paragraph(
                runs=(BookmarkStart(name="table-anchor"),),
                formatting=ParagraphFormatting(),
            ),),
        )
        row = TableRow(cells=(cell,))
        table = Table(rows=(row,))
        xml = _xml(_doc(body=(table,)))
        assert "bookmarkStart" in xml
        assert 'w:name="table-anchor"' in xml
