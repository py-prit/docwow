"""Integration tests: TOC round-trip DOCX → HTML → DOCX."""
from __future__ import annotations

import io

import pytest

from docwow.api._convert import document_to_frozen
from docwow.api.document import DocumentWrapper
from docwow.api.toc import MutableTableOfContents
from docwow.html_parser.html_parser import parse_html
from docwow.models.toc import TableOfContents
from docwow.renderer.html_renderer import render_document


def _make_doc_with_toc() -> DocumentWrapper:
    doc = DocumentWrapper()
    doc.paragraphs.add_paragraph("Introduction").set_style("Heading1")
    toc = doc.paragraphs.add_toc("Contents")
    toc.add_entry("Introduction", url="#_Toc1", level=1)
    toc.add_entry("Background", url="#_Toc2", level=2)
    doc.paragraphs.add_paragraph("Body text here.")
    return doc


class TestTocRoundTrip:
    def test_toc_survives_html_round_trip(self):
        doc = _make_doc_with_toc()
        frozen = document_to_frozen(doc)
        html = render_document(frozen)
        recovered = parse_html(html)
        toc_elements = [e for e in recovered.body if isinstance(e, TableOfContents)]
        assert len(toc_elements) == 1

    def test_toc_title_survives_round_trip(self):
        doc = _make_doc_with_toc()
        frozen = document_to_frozen(doc)
        html = render_document(frozen)
        recovered = parse_html(html)
        toc = next(e for e in recovered.body if isinstance(e, TableOfContents))
        assert toc.title == "Contents"

    def test_toc_entries_survive_round_trip(self):
        doc = _make_doc_with_toc()
        frozen = document_to_frozen(doc)
        html = render_document(frozen)
        recovered = parse_html(html)
        toc = next(e for e in recovered.body if isinstance(e, TableOfContents))
        assert len(toc.entries) == 2

    def test_toc_entry_text_survives(self):
        doc = _make_doc_with_toc()
        frozen = document_to_frozen(doc)
        html = render_document(frozen)
        recovered = parse_html(html)
        toc = next(e for e in recovered.body if isinstance(e, TableOfContents))
        assert toc.entries[0].text == "Introduction"

    def test_toc_entry_url_survives(self):
        doc = _make_doc_with_toc()
        frozen = document_to_frozen(doc)
        html = render_document(frozen)
        recovered = parse_html(html)
        toc = next(e for e in recovered.body if isinstance(e, TableOfContents))
        assert toc.entries[0].url == "#_Toc1"

    def test_toc_entry_level_survives(self):
        doc = _make_doc_with_toc()
        frozen = document_to_frozen(doc)
        html = render_document(frozen)
        recovered = parse_html(html)
        toc = next(e for e in recovered.body if isinstance(e, TableOfContents))
        assert toc.entries[0].level == 1
        assert toc.entries[1].level == 2

    def test_other_paragraphs_preserved(self):
        doc = _make_doc_with_toc()
        frozen = document_to_frozen(doc)
        html = render_document(frozen)
        recovered = parse_html(html)
        non_toc = [e for e in recovered.body if not isinstance(e, TableOfContents)]
        assert len(non_toc) >= 2  # heading + body text


class TestTocFromFrozen:
    def test_toc_from_frozen_conversion(self):
        from docwow.api._convert import toc_from_frozen, document_from_frozen
        from docwow.models.toc import TableOfContents, TocEntry

        frozen_toc = TableOfContents(
            title="My TOC",
            entries=(
                TocEntry(text="Intro", url="#_Toc1", level=1),
                TocEntry(text="BG", url="#_Toc2", level=2),
            ),
        )
        mutable = toc_from_frozen(frozen_toc)
        assert isinstance(mutable, MutableTableOfContents)
        assert mutable.title == "My TOC"
        assert len(mutable.entries) == 2
        assert mutable.entries[0].text == "Intro"

    def test_document_from_frozen_with_toc(self):
        from docwow.api._convert import document_from_frozen
        from docwow.models.document import Document
        from docwow.models.toc import TableOfContents, TocEntry

        frozen_doc = Document(
            body=(TableOfContents(
                title="TOC",
                entries=(TocEntry(text="Intro", url="#_Toc1", level=1),),
            ),),
            styles=(),
            numbering=(),
        )
        wrapper = document_from_frozen(frozen_doc)
        toc_items = [
            item for item in wrapper.paragraphs
            if isinstance(item, MutableTableOfContents)
        ]
        assert len(toc_items) == 1
        assert toc_items[0].title == "TOC"
