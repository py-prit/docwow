"""Tests for document field codes: DATE, TIME, AUTHOR, TITLE, FILENAME."""

from __future__ import annotations

from pathlib import Path

import docwow
from docwow.api.document import DocumentWrapper
from docwow.api.run import MutablePageNumberField

FIXTURES = Path(__file__).parent.parent / "fixtures"

_METADATA_FIELDS = ("DATE", "TIME", "AUTHOR", "TITLE", "FILENAME")
_ALL_FIELDS = ("PAGE", "NUMPAGES", "SECTIONPAGES") + _METADATA_FIELDS


class TestFieldParsing:
    def test_date_field_round_trips_docx(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph()
        para.runs.add_page_number("DATE")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = doc2.paragraphs[0]
        fields = [r for r in para2.runs if isinstance(r, MutablePageNumberField)]
        assert len(fields) == 1
        assert fields[0].field_type == "DATE"

    def test_author_field_round_trips_docx(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph()
        para.runs.add_page_number("AUTHOR")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = doc2.paragraphs[0]
        fields = [r for r in para2.runs if isinstance(r, MutablePageNumberField)]
        assert fields[0].field_type == "AUTHOR"

    def test_title_field_round_trips_docx(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph()
        para.runs.add_page_number("TITLE")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = doc2.paragraphs[0]
        fields = [r for r in para2.runs if isinstance(r, MutablePageNumberField)]
        assert fields[0].field_type == "TITLE"


class TestFieldRendering:
    def _html_with_field(self, field_type: str) -> str:
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph().runs.add_page_number(field_type)
        return doc.to_html()

    def test_date_renders_placeholder(self):
        html = self._html_with_field("DATE")
        assert 'data-dw-field="DATE"' in html
        assert "1/1/2000" in html

    def test_time_renders_placeholder(self):
        html = self._html_with_field("TIME")
        assert 'data-dw-field="TIME"' in html
        assert "12:00 PM" in html

    def test_author_renders_placeholder(self):
        html = self._html_with_field("AUTHOR")
        assert 'data-dw-field="AUTHOR"' in html
        assert "Author" in html

    def test_title_renders_placeholder(self):
        html = self._html_with_field("TITLE")
        assert 'data-dw-field="TITLE"' in html
        assert "Title" in html

    def test_filename_renders_placeholder(self):
        html = self._html_with_field("FILENAME")
        assert 'data-dw-field="FILENAME"' in html
        assert "document.docx" in html

    def test_all_fields_render_dw_field_span(self):
        for ft in _ALL_FIELDS:
            html = self._html_with_field(ft)
            assert f'data-dw-field="{ft}"' in html, f"Missing data-dw-field for {ft}"


class TestFieldHtmlRoundTrip:
    def test_date_survives_html_round_trip(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph().runs.add_page_number("DATE")

        html = doc.to_html()
        data = docwow.to_docx(html)
        doc2 = docwow.open(data)
        para = doc2.paragraphs[0]
        fields = [r for r in para.runs if isinstance(r, MutablePageNumberField)]
        assert fields[0].field_type == "DATE"

    def test_author_survives_html_round_trip(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph().runs.add_page_number("AUTHOR")

        html = doc.to_html()
        data = docwow.to_docx(html)
        doc2 = docwow.open(data)
        para = doc2.paragraphs[0]
        fields = [r for r in para.runs if isinstance(r, MutablePageNumberField)]
        assert fields[0].field_type == "AUTHOR"
