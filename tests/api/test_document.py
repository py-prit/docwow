"""Tests for DocumentWrapper."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from docwow.api.document import DocumentWrapper
from docwow.api.paragraph import ParagraphCollection


class TestDocumentWrapperConstruction:
    def test_defaults(self):
        doc = DocumentWrapper()
        assert len(doc.paragraphs) == 0
        assert doc.page_width_pt == pytest.approx(595.28)
        assert doc.page_height_pt == pytest.approx(841.89)
        assert doc.margin_top_pt == 72.0
        assert doc.margin_bottom_pt == 72.0
        assert doc.margin_left_pt == 72.0
        assert doc.margin_right_pt == 72.0

    def test_custom_geometry(self):
        doc = DocumentWrapper(
            page_width_pt=612.0,
            page_height_pt=792.0,
            margin_top_pt=36.0,
        )
        assert doc.page_width_pt == 612.0
        assert doc.page_height_pt == 792.0
        assert doc.margin_top_pt == 36.0

    def test_paragraphs_is_collection(self):
        doc = DocumentWrapper()
        assert isinstance(doc.paragraphs, ParagraphCollection)


class TestDocumentWrapperMutation:
    def test_set_page_size(self):
        doc = DocumentWrapper()
        result = doc.set_page_size(612.0, 792.0)
        assert doc.page_width_pt == 612.0
        assert doc.page_height_pt == 792.0
        assert result is doc

    def test_set_margins(self):
        doc = DocumentWrapper()
        result = doc.set_margins(top_pt=36.0, bottom_pt=36.0, left_pt=54.0, right_pt=54.0)
        assert doc.margin_top_pt == 36.0
        assert doc.margin_bottom_pt == 36.0
        assert doc.margin_left_pt == 54.0
        assert doc.margin_right_pt == 54.0
        assert result is doc


class TestDocumentWrapperNumbering:
    def test_add_numbering_definition(self):
        doc = DocumentWrapper()
        num_id = doc.add_numbering_definition("bullet")
        assert isinstance(num_id, str)
        assert len(doc._numbering) == 1

    def test_add_multiple_definitions(self):
        doc = DocumentWrapper()
        id1 = doc.add_numbering_definition("bullet")
        id2 = doc.add_numbering_definition("decimal")
        assert id1 != id2
        assert len(doc._numbering) == 2


class TestDocumentWrapperToFrozen:
    def test_produces_document(self, empty_doc):
        from docwow.models.document import Document
        frozen = empty_doc._to_frozen()
        assert isinstance(frozen, Document)

    def test_body_elements(self, simple_doc):
        frozen = simple_doc._to_frozen()
        assert len(frozen.body) == 1

    def test_geometry_preserved(self):
        doc = DocumentWrapper(page_width_pt=612.0, margin_top_pt=36.0)
        frozen = doc._to_frozen()
        assert frozen.page_width_pt == 612.0
        assert frozen.margin_top_pt == 36.0


class TestDocumentWrapperToBytes:
    def test_returns_bytes(self, simple_doc):
        data = simple_doc.to_bytes()
        assert isinstance(data, bytes)

    def test_valid_zip(self, simple_doc):
        data = simple_doc.to_bytes()
        assert zipfile.is_zipfile(__import__("io").BytesIO(data))

    def test_empty_document(self, empty_doc):
        data = empty_doc.to_bytes()
        assert isinstance(data, bytes)
        assert len(data) > 0


class TestDocumentWrapperSave:
    def test_writes_file(self, simple_doc, tmp_path):
        out = tmp_path / "output.docx"
        simple_doc.save(out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_written_file_is_valid_zip(self, simple_doc, tmp_path):
        out = tmp_path / "output.docx"
        simple_doc.save(out)
        assert zipfile.is_zipfile(out)

    def test_accepts_string_path(self, simple_doc, tmp_path):
        out = str(tmp_path / "output.docx")
        simple_doc.save(out)
        assert Path(out).exists()


class TestDocumentWrapperToHtml:
    def test_returns_string(self, simple_doc):
        html = simple_doc.to_html()
        assert isinstance(html, str)

    def test_contains_doctype(self, simple_doc):
        html = simple_doc.to_html()
        assert "<!DOCTYPE" in html or "<html" in html

    def test_contains_text(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("unique_marker_xyz")
        html = doc.to_html()
        assert "unique_marker_xyz" in html


class TestDocumentWrapperRepr:
    def test_repr(self, simple_doc):
        r = repr(simple_doc)
        assert "DocumentWrapper" in r
