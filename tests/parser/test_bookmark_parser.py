"""Tests for bookmark parsing in docwow.parser.body_parser."""
from __future__ import annotations

import io
import zipfile

import pytest
from lxml import etree

from docwow.models.paragraph import BookmarkStart, Paragraph, TextRun
from docwow.parser.body_parser import _parse_paragraph

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _empty_zip() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


def _p_el(inner_xml: str) -> etree._Element:
    """Wrap inner XML in a <w:p> element."""
    return etree.fromstring(
        f'<w:p xmlns:w="{_W}">{inner_xml}</w:p>'
    )


def _parse(inner_xml: str) -> Paragraph:
    return _parse_paragraph(_p_el(inner_xml), _empty_zip(), {})


# ---------------------------------------------------------------------------
# Bookmark parsing
# ---------------------------------------------------------------------------

class TestBookmarkStartParsed:
    def test_bookmark_start_produces_bookmark_start_run(self):
        para = _parse('<w:bookmarkStart w:id="0" w:name="intro"/>')
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 1

    def test_bookmark_name_extracted(self):
        para = _parse('<w:bookmarkStart w:id="0" w:name="mySection"/>')
        bm = next(r for r in para.runs if isinstance(r, BookmarkStart))
        assert bm.name == "mySection"

    def test_bookmark_end_is_skipped(self):
        para = _parse(
            '<w:bookmarkStart w:id="0" w:name="x"/>'
            '<w:bookmarkEnd w:id="0"/>'
        )
        # Only one run: the BookmarkStart; the BookmarkEnd produces nothing
        assert len(para.runs) == 1
        assert isinstance(para.runs[0], BookmarkStart)

    def test_bookmark_before_text(self):
        para = _parse(
            '<w:bookmarkStart w:id="0" w:name="anchor"/>'
            '<w:r><w:t>Hello</w:t></w:r>'
        )
        assert isinstance(para.runs[0], BookmarkStart)
        assert isinstance(para.runs[1], TextRun)
        assert para.runs[1].text == "Hello"

    def test_bookmark_after_text(self):
        para = _parse(
            '<w:r><w:t>Hello</w:t></w:r>'
            '<w:bookmarkStart w:id="1" w:name="end-anchor"/>'
        )
        assert isinstance(para.runs[0], TextRun)
        assert isinstance(para.runs[1], BookmarkStart)

    def test_multiple_bookmarks(self):
        para = _parse(
            '<w:bookmarkStart w:id="0" w:name="first"/>'
            '<w:r><w:t>text</w:t></w:r>'
            '<w:bookmarkStart w:id="1" w:name="second"/>'
        )
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 2
        assert bm_runs[0].name == "first"
        assert bm_runs[1].name == "second"

    def test_bookmark_without_name_skipped(self):
        # w:bookmarkStart with no w:name attribute → skipped
        para = _parse('<w:bookmarkStart w:id="0"/>')
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 0

    def test_internal_bookmark_skipped(self):
        # Bookmarks starting with "_" (Word internal, e.g. _GoBack) are skipped
        para = _parse('<w:bookmarkStart w:id="0" w:name="_GoBack"/>')
        bm_runs = [r for r in para.runs if isinstance(r, BookmarkStart)]
        assert len(bm_runs) == 0
