"""Integration tests — full DOCX → HTML → DOCX round-trip for bookmarks."""
from __future__ import annotations

import io

import pytest

import docwow
from docwow.api.document import DocumentWrapper
from docwow.api.run import MutableBookmark
from docwow.models.paragraph import BookmarkStart


class TestBookmarkRoundTrip:
    """Build a document with bookmarks via the API, save it, reload it."""

    @pytest.fixture(scope="class")
    def round_trip_doc(self):
        """Create a doc with bookmarks, save to bytes, reload."""
        doc = DocumentWrapper()
        p = doc.paragraphs.add_paragraph()
        p.runs.add_bookmark("intro")
        p.runs.add_text("Introduction")

        p2 = doc.paragraphs.add_paragraph()
        p2.runs.add_text("A hyperlink: ")
        p2.runs.add_hyperlink("go to intro", "#intro")

        docx_bytes = doc.to_bytes()
        return docwow.open(docx_bytes)

    def test_bookmark_preserved_after_round_trip(self, round_trip_doc):
        from docwow.api.run import MutableBookmark
        bm_runs = [
            r
            for p in round_trip_doc.paragraphs
            for r in p.runs
            if isinstance(r, MutableBookmark)
        ]
        assert len(bm_runs) >= 1

    def test_bookmark_name_preserved(self, round_trip_doc):
        from docwow.api.run import MutableBookmark
        bm_runs = [
            r
            for p in round_trip_doc.paragraphs
            for r in p.runs
            if isinstance(r, MutableBookmark)
        ]
        assert bm_runs[0].name == "intro"

    def test_text_preserved_alongside_bookmark(self, round_trip_doc):
        from docwow.api.run import MutableRun
        texts = [
            r.get_text()
            for p in round_trip_doc.paragraphs
            for r in p.runs
            if isinstance(r, MutableRun)
        ]
        assert "Introduction" in texts


class TestBookmarkHTMLOutput:
    """Verify the HTML output of a document with bookmarks."""

    @pytest.fixture(scope="class")
    def html(self):
        doc = DocumentWrapper()
        p = doc.paragraphs.add_paragraph()
        p.runs.add_bookmark("chapter1")
        p.runs.add_text("Chapter One")
        return doc.to_html()

    def test_html_contains_bookmark_anchor(self, html):
        assert 'id="chapter1"' in html

    def test_html_has_dw_bookmark_class(self, html):
        assert 'class="dw-bookmark"' in html

    def test_html_has_data_attribute(self, html):
        assert 'data-dw-bookmark="chapter1"' in html

    def test_html_contains_paragraph_text(self, html):
        assert "Chapter One" in html


class TestBookmarkHTMLRoundTrip:
    """DOCX → HTML → DOCX via to_html / from_html."""

    @pytest.fixture(scope="class")
    def html(self):
        doc = DocumentWrapper()
        p = doc.paragraphs.add_paragraph()
        p.runs.add_bookmark("section2")
        p.runs.add_text("Section Two")
        return doc.to_html()

    def test_bookmark_survives_html_round_trip(self, html):
        """Parse HTML back to a Document and verify bookmark is present."""
        from docwow.html_parser.html_parser import parse_html
        from docwow.models.paragraph import BookmarkStart, Paragraph

        doc = parse_html(html)
        bm_runs = [
            r
            for elem in doc.body
            if isinstance(elem, Paragraph)
            for r in elem.runs
            if isinstance(r, BookmarkStart)
        ]
        assert len(bm_runs) >= 1
        assert bm_runs[0].name == "section2"
