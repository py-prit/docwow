"""End-to-end integration tests for the mutable API layer."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

import docwow
from docwow.api.document import DocumentWrapper
from docwow.api.list_item import MutableListItem
from docwow.api.paragraph import MutableParagraph
from docwow.api.table import TableView

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestOpenReturnsWrapper:
    def test_open_docx_file_returns_wrapper(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        assert isinstance(doc, DocumentWrapper)

    def test_open_docx_bytes_returns_wrapper(self):
        data = (FIXTURES / "paragraphs.docx").read_bytes()
        doc = docwow.open(data)
        assert isinstance(doc, DocumentWrapper)

    def test_open_has_paragraphs(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        assert len(doc.paragraphs) > 0

    def test_open_table_docx(self):
        doc = docwow.open(FIXTURES / "table_simple.docx")
        tables = [p for p in doc.paragraphs if isinstance(p, TableView)]
        assert len(tables) > 0

    def test_open_list_docx(self):
        doc = docwow.open(FIXTURES / "list_bullet.docx")
        items = [p for p in doc.paragraphs if isinstance(p, MutableListItem)]
        assert len(items) > 0


class TestTextPreservation:
    def test_get_text_from_opened_doc(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        texts = [p.get_text() for p in doc.paragraphs if isinstance(p, MutableParagraph)]
        combined = " ".join(texts)
        assert len(combined) > 0

    def test_paragraph_count_matches(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        paras = [p for p in doc.paragraphs if isinstance(p, MutableParagraph)]
        assert len(paras) > 0


class TestMutateAndRoundtrip:
    def test_change_text_roundtrip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        first_para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        first_para.set_text("REPLACED_TEXT_XYZ")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        texts = [p.get_text() for p in doc2.paragraphs if isinstance(p, MutableParagraph)]
        assert "REPLACED_TEXT_XYZ" in texts

    def test_set_bold_roundtrip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        first_para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        first_para.set_text("bold test")
        first_para.set_bold(True)

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        first_para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        assert all(r.bold for r in first_para2.runs)

    def test_add_paragraph_roundtrip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        doc.paragraphs.add_paragraph("BRAND_NEW_PARA_ABC")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        texts = [p.get_text() for p in doc2.paragraphs if isinstance(p, MutableParagraph)]
        assert "BRAND_NEW_PARA_ABC" in texts

    def test_add_list_item_roundtrip(self):
        doc = docwow.open(FIXTURES / "list_bullet.docx")
        doc.paragraphs.add_list_item("NEW_LIST_ITEM_XYZ", level=0)

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        items = [p for p in doc2.paragraphs if isinstance(p, MutableListItem)]
        texts = [i.get_text() for i in items]
        assert "NEW_LIST_ITEM_XYZ" in texts

    def test_set_style_roundtrip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        first_para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        first_para.set_style("Heading1")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        first_para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        assert first_para2.style_id == "Heading1"

    def test_chained_mutations(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        first_para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        first_para.set_text("chained").set_bold(True).set_italic(True).set_style("Normal")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        first_para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        assert first_para2.get_text() == "chained"
        assert first_para2.style_id == "Normal"


class TestTableReadOnly:
    def test_table_accessible(self):
        doc = docwow.open(FIXTURES / "table_simple.docx")
        tables = [p for p in doc.paragraphs if isinstance(p, TableView)]
        assert len(tables) > 0
        table = tables[0]
        assert len(table) > 0

    def test_table_cell_text_readable(self):
        doc = docwow.open(FIXTURES / "table_simple.docx")
        table = next(p for p in doc.paragraphs if isinstance(p, TableView))
        text = table[0][0].get_text()
        assert isinstance(text, str)

    def test_table_has_mutation_methods(self):
        doc = docwow.open(FIXTURES / "table_simple.docx")
        table = next(p for p in doc.paragraphs if isinstance(p, TableView))
        assert hasattr(table, "append")
        assert hasattr(table, "insert")
        assert hasattr(table, "remove")
        assert hasattr(table, "add_row")

    def test_table_preserved_in_roundtrip(self):
        doc = docwow.open(FIXTURES / "table_simple.docx")
        initial_tables = sum(1 for p in doc.paragraphs if isinstance(p, TableView))

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        final_tables = sum(1 for p in doc2.paragraphs if isinstance(p, TableView))
        assert final_tables == initial_tables


class TestEmptyDocument:
    def test_empty_wrapper_to_bytes(self):
        doc = DocumentWrapper()
        data = doc.to_bytes()
        assert isinstance(data, bytes)
        assert zipfile.is_zipfile(__import__("io").BytesIO(data))

    def test_empty_wrapper_to_html(self):
        doc = DocumentWrapper()
        html = doc.to_html()
        assert isinstance(html, str)

    def test_build_from_scratch(self, tmp_path):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("Title", style_id="Heading1")
        doc.paragraphs.add_paragraph("Body text here.")
        doc.paragraphs.add_paragraph("Second paragraph.")

        out = tmp_path / "scratch.docx"
        doc.save(out)
        assert out.exists()

        doc2 = docwow.open(out)
        texts = [p.get_text() for p in doc2.paragraphs if isinstance(p, MutableParagraph)]
        assert "Title" in texts
        assert "Body text here." in texts


class TestToHtml:
    def test_wrapper_to_html(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        html = doc.to_html()
        assert isinstance(html, str)
        assert len(html) > 0

    def test_html_contains_text(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("hello_unique_string")
        html = doc.to_html()
        assert "hello_unique_string" in html
