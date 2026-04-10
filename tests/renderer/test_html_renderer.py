"""Tests for docwow.renderer.html_renderer — render_document()."""
import pytest
from docwow.models.document import Document
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, Style
from docwow.models.table import Table, TableCell, TableRow
from docwow.renderer.html_renderer import render_document, _document_attrs, _render_body


def _doc(body=(), styles=(), numbering=(), **kwargs):
    defaults = dict(
        page_width_pt=595.28, page_height_pt=841.89,
        margin_top_pt=72.0, margin_bottom_pt=72.0,
        margin_left_pt=72.0, margin_right_pt=72.0,
    )
    defaults.update(kwargs)
    return Document(body=body, styles=styles, numbering=numbering, **defaults)


def _para(text="Hello", list_info=None):
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(),
        list_info=list_info,
    )


def _list_para(text, num_id="1", level=0):
    return _para(text, list_info=ListInfo(num_id=num_id, level=level))


def _simple_table():
    p = _para("cell")
    cell = TableCell(paragraphs=(p,))
    row = TableRow(cells=(cell,))
    return Table(rows=(row,))


class TestRenderDocumentStructure:
    def test_starts_with_doctype(self):
        assert render_document(_doc()).startswith("<!DOCTYPE html>")

    def test_contains_html_tag(self):
        html = render_document(_doc())
        assert "<html" in html
        assert "</html>" in html

    def test_contains_head_tag(self):
        html = render_document(_doc())
        assert "<head>" in html
        assert "</head>" in html

    def test_contains_style_tag(self):
        html = render_document(_doc())
        assert "<style>" in html
        assert "</style>" in html

    def test_contains_body_tag(self):
        html = render_document(_doc())
        assert "<body>" in html
        assert "</body>" in html

    def test_contains_dw_document_div(self):
        html = render_document(_doc())
        assert 'class="dw-document"' in html

    def test_charset_meta(self):
        assert 'charset="UTF-8"' in render_document(_doc())

    def test_lang_attribute(self):
        assert 'lang="en"' in render_document(_doc())


class TestDocumentDataAttrs:
    def test_page_width_attr(self):
        html = render_document(_doc(page_width_pt=595.28))
        assert 'data-dw-page-width="595.28pt"' in html

    def test_page_height_attr(self):
        html = render_document(_doc(page_height_pt=841.89))
        assert 'data-dw-page-height="841.89pt"' in html

    def test_margin_top_attr(self):
        html = render_document(_doc(margin_top_pt=72.0))
        assert 'data-dw-margin-top="72pt"' in html

    def test_margin_bottom_attr(self):
        assert 'data-dw-margin-bottom="72pt"' in render_document(_doc())

    def test_margin_left_attr(self):
        assert 'data-dw-margin-left="72pt"' in render_document(_doc())

    def test_margin_right_attr(self):
        assert 'data-dw-margin-right="72pt"' in render_document(_doc())

    def test_letter_page_size(self):
        html = render_document(_doc(page_width_pt=612.0, page_height_pt=792.0))
        assert 'data-dw-page-width="612pt"' in html
        assert 'data-dw-page-height="792pt"' in html


class TestRenderBodyParagraphs:
    def test_paragraph_rendered(self):
        doc = _doc(body=(_para("Test text"),))
        assert "Test text" in render_document(doc)

    def test_multiple_paragraphs(self):
        doc = _doc(body=(_para("First"), _para("Second")))
        html = render_document(doc)
        assert "First" in html
        assert "Second" in html

    def test_empty_body(self):
        html = render_document(_doc())
        assert "dw-document" in html  # still has the wrapper

    def test_paragraph_tag_present(self):
        doc = _doc(body=(_para("text"),))
        assert "<p " in render_document(doc)


class TestRenderBodyTables:
    def test_table_rendered(self):
        doc = _doc(body=(_simple_table(),))
        assert "<table " in render_document(doc)

    def test_mixed_body(self):
        doc = _doc(body=(_para("before"), _simple_table(), _para("after")))
        html = render_document(doc)
        assert "before" in html
        assert "<table " in html
        assert "after" in html


class TestRenderBodyLists:
    def test_list_paragraph_produces_ul(self):
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        ),)
        doc = _doc(body=(_list_para("Item"),), numbering=nd)
        assert "<ul " in render_document(doc)

    def test_list_paragraph_produces_li(self):
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        ),)
        doc = _doc(body=(_list_para("Item"),), numbering=nd)
        assert "<li " in render_document(doc)

    def test_list_flushed_before_non_list(self):
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        ),)
        doc = _doc(body=(
            _list_para("List item"),
            _para("Normal after list"),
        ), numbering=nd)
        html = render_document(doc)
        # Both should appear; list must close before normal paragraph
        list_pos = html.index("</ul>")
        para_pos = html.index("Normal after list")
        assert list_pos < para_pos

    def test_css_included_in_output(self):
        html = render_document(_doc())
        assert ".dw-p" in html
        assert ".dw-table" in html


class TestDocumentAttrsHelper:
    def test_contains_class(self):
        assert 'class="dw-document"' in _document_attrs(_doc())

    def test_all_six_data_attrs(self):
        attrs = _document_attrs(_doc())
        assert "data-dw-page-width" in attrs
        assert "data-dw-page-height" in attrs
        assert "data-dw-margin-top" in attrs
        assert "data-dw-margin-bottom" in attrs
        assert "data-dw-margin-left" in attrs
        assert "data-dw-margin-right" in attrs
