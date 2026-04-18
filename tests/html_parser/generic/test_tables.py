"""Tests for generic HTML table parsing (table/tr/td/th, colspan/rowspan)."""
from __future__ import annotations

import pytest

from docwow.html_parser.generic.html_parser import parse_foreign_html
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.table import Table, TableCell, TableRow


def _parse(html: str):
    return parse_foreign_html(html)


def _table(html: str) -> Table:
    doc = _parse(html)
    tables = [el for el in doc.body if isinstance(el, Table)]
    assert tables, "No table found in parsed output"
    return tables[0]


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------

class TestBasicTable:
    def test_single_cell(self):
        t = _table("<table><tr><td>Hello</td></tr></table>")
        assert len(t.rows) == 1
        assert len(t.rows[0].cells) == 1

    def test_cell_text(self):
        t = _table("<table><tr><td>Hello</td></tr></table>")
        cell = t.rows[0].cells[0]
        assert cell.paragraphs[0].runs[0].text == "Hello"

    def test_two_rows(self):
        t = _table("<table><tr><td>A</td></tr><tr><td>B</td></tr></table>")
        assert len(t.rows) == 2

    def test_two_columns(self):
        t = _table("<table><tr><td>A</td><td>B</td></tr></table>")
        assert len(t.rows[0].cells) == 2

    def test_style_id_is_table_grid(self):
        t = _table("<table><tr><td>X</td></tr></table>")
        assert t.style_id == "TableGrid"

    def test_cell_has_at_least_one_paragraph(self):
        t = _table("<table><tr><td></td></tr></table>")
        assert len(t.rows[0].cells[0].paragraphs) >= 1

    def test_table_in_document_body(self):
        doc = _parse("<p>Before</p><table><tr><td>A</td></tr></table><p>After</p>")
        types = [type(el).__name__ for el in doc.body]
        assert "Table" in types
        assert types.index("Table") == 1


# ---------------------------------------------------------------------------
# <th> header cells
# ---------------------------------------------------------------------------

class TestHeaderCells:
    def test_th_makes_bold(self):
        t = _table("<table><tr><th>Header</th></tr></table>")
        run = t.rows[0].cells[0].paragraphs[0].runs[0]
        assert isinstance(run, TextRun)
        assert run.formatting.bold is True

    def test_td_not_bold_by_default(self):
        t = _table("<table><tr><td>Data</td></tr></table>")
        run = t.rows[0].cells[0].paragraphs[0].runs[0]
        assert isinstance(run, TextRun)
        assert not run.formatting.bold

    def test_mixed_th_and_td(self):
        t = _table("<table><tr><th>H1</th><th>H2</th></tr><tr><td>D1</td><td>D2</td></tr></table>")
        assert t.rows[0].cells[0].paragraphs[0].runs[0].formatting.bold
        assert t.rows[0].cells[1].paragraphs[0].runs[0].formatting.bold
        assert not t.rows[1].cells[0].paragraphs[0].runs[0].formatting.bold


# ---------------------------------------------------------------------------
# thead / tbody / tfoot sections
# ---------------------------------------------------------------------------

class TestTableSections:
    def test_tbody(self):
        t = _table("<table><tbody><tr><td>A</td></tr></tbody></table>")
        assert len(t.rows) == 1
        assert t.rows[0].cells[0].paragraphs[0].runs[0].text == "A"

    def test_thead_and_tbody(self):
        html = (
            "<table>"
            "<thead><tr><th>Name</th><th>Score</th></tr></thead>"
            "<tbody><tr><td>Alice</td><td>95</td></tr></tbody>"
            "</table>"
        )
        t = _table(html)
        assert len(t.rows) == 2
        assert t.rows[0].cells[0].paragraphs[0].runs[0].formatting.bold  # th
        assert t.rows[1].cells[0].paragraphs[0].runs[0].text == "Alice"

    def test_tfoot_rows_included(self):
        html = (
            "<table>"
            "<tbody><tr><td>Body</td></tr></tbody>"
            "<tfoot><tr><td>Total</td></tr></tfoot>"
            "</table>"
        )
        t = _table(html)
        assert len(t.rows) == 2


# ---------------------------------------------------------------------------
# colspan
# ---------------------------------------------------------------------------

class TestColspan:
    def test_colspan_sets_col_span(self):
        t = _table("<table><tr><td colspan='2'>Wide</td></tr></table>")
        assert t.rows[0].cells[0].col_span == 2

    def test_colspan_row_has_one_cell(self):
        t = _table("<table><tr><td colspan='3'>Wide</td></tr></table>")
        assert len(t.rows[0].cells) == 1

    def test_following_row_has_normal_cells(self):
        html = (
            "<table>"
            "<tr><td colspan='2'>Wide</td></tr>"
            "<tr><td>A</td><td>B</td></tr>"
            "</table>"
        )
        t = _table(html)
        assert len(t.rows[1].cells) == 2

    def test_colspan_content_preserved(self):
        t = _table("<table><tr><td colspan='2'>Content</td></tr></table>")
        assert t.rows[0].cells[0].paragraphs[0].runs[0].text == "Content"

    def test_no_col_span_on_normal_cell(self):
        t = _table("<table><tr><td>A</td><td>B</td></tr></table>")
        assert t.rows[0].cells[0].col_span == 1
        assert t.rows[0].cells[1].col_span == 1


# ---------------------------------------------------------------------------
# rowspan
# ---------------------------------------------------------------------------

class TestRowspan:
    def test_rowspan_sets_v_merge_start(self):
        html = "<table><tr><td rowspan='2'>Tall</td><td>R0</td></tr><tr><td>R1</td></tr></table>"
        t = _table(html)
        assert t.rows[0].cells[0].v_merge_start is True

    def test_continuation_row_has_v_merge_continue(self):
        html = "<table><tr><td rowspan='2'>Tall</td><td>R0</td></tr><tr><td>R1</td></tr></table>"
        t = _table(html)
        assert t.rows[1].cells[0].v_merge_continue is True

    def test_continuation_cell_has_empty_paragraph(self):
        html = "<table><tr><td rowspan='2'>Tall</td><td>R0</td></tr><tr><td>R1</td></tr></table>"
        t = _table(html)
        cont_cell = t.rows[1].cells[0]
        assert cont_cell.v_merge_continue
        assert len(cont_cell.paragraphs) >= 1

    def test_three_row_span(self):
        html = (
            "<table>"
            "<tr><td rowspan='3'>Big</td><td>R0</td></tr>"
            "<tr><td>R1</td></tr>"
            "<tr><td>R2</td></tr>"
            "</table>"
        )
        t = _table(html)
        assert t.rows[0].cells[0].v_merge_start
        assert t.rows[1].cells[0].v_merge_continue
        assert t.rows[2].cells[0].v_merge_continue

    def test_non_spanned_cells_correct(self):
        html = "<table><tr><td rowspan='2'>Tall</td><td>R0C1</td></tr><tr><td>R1C1</td></tr></table>"
        t = _table(html)
        assert t.rows[0].cells[1].paragraphs[0].runs[0].text == "R0C1"
        assert t.rows[1].cells[1].paragraphs[0].runs[0].text == "R1C1"

    def test_rowspan_one_is_normal(self):
        t = _table("<table><tr><td rowspan='1'>A</td></tr></table>")
        assert t.rows[0].cells[0].v_merge_start is False
        assert t.rows[0].cells[0].v_merge_continue is False


# ---------------------------------------------------------------------------
# Cell content
# ---------------------------------------------------------------------------

class TestCellContent:
    def test_inline_bold_in_cell(self):
        t = _table("<table><tr><td><b>bold</b></td></tr></table>")
        runs = t.rows[0].cells[0].paragraphs[0].runs
        assert any(isinstance(r, TextRun) and r.formatting.bold for r in runs)

    def test_multiple_paragraphs_in_cell(self):
        t = _table("<table><tr><td><p>First</p><p>Second</p></td></tr></table>")
        assert len(t.rows[0].cells[0].paragraphs) == 2

    def test_cell_background_color(self):
        t = _table('<table><tr><td style="background-color: #FF0000">Red</td></tr></table>')
        assert t.rows[0].cells[0].shading == "FF0000"

    def test_cell_no_shading_by_default(self):
        t = _table("<table><tr><td>Plain</td></tr></table>")
        assert t.rows[0].cells[0].shading is None


# ---------------------------------------------------------------------------
# colgroup / column widths
# ---------------------------------------------------------------------------

class TestColWidths:
    def test_colgroup_widths_captured(self):
        html = (
            "<table>"
            "<colgroup>"
            "<col style='width: 100pt'>"
            "<col style='width: 200pt'>"
            "</colgroup>"
            "<tr><td>A</td><td>B</td></tr>"
            "</table>"
        )
        t = _table(html)
        assert t.col_widths_pt == (100.0, 200.0)

    def test_no_colgroup_auto_distributes_evenly(self):
        # Without a <colgroup>, columns get equal shares of the default text width.
        t = _table("<table><tr><td>A</td><td>B</td></tr></table>")
        assert len(t.col_widths_pt) == 2
        assert t.col_widths_pt[0] == t.col_widths_pt[1]


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_docx_roundtrip_basic(self):
        import docwow
        html = (
            "<table>"
            "<tr><th>Name</th><th>Score</th></tr>"
            "<tr><td>Alice</td><td>95</td></tr>"
            "<tr><td>Bob</td><td>87</td></tr>"
            "</table>"
        )
        docx_bytes = docwow.to_docx(html, is_foreign_html=True)
        assert len(docx_bytes) > 0

        doc = docwow.open(docx_bytes)
        from docwow.api.table import MutableTable
        tables = [el for el in doc.paragraphs if isinstance(el, MutableTable)]
        assert len(tables) == 1
        tbl = tables[0]
        assert len(tbl) == 3  # 3 rows

    def test_docx_roundtrip_colspan(self):
        import docwow
        html = (
            "<table>"
            "<tr><td colspan='2'>Wide header</td></tr>"
            "<tr><td>A</td><td>B</td></tr>"
            "</table>"
        )
        docx_bytes = docwow.to_docx(html, is_foreign_html=True)
        doc = docwow.open(docx_bytes)
        from docwow.api.table import MutableTable
        tbl = next(el for el in doc.paragraphs if isinstance(el, MutableTable))
        assert tbl[0][0].col_span == 2

    def test_table_and_paragraphs_coexist(self):
        import docwow
        html = (
            "<p>Before</p>"
            "<table><tr><td>Cell</td></tr></table>"
            "<p>After</p>"
        )
        docx_bytes = docwow.to_docx(html, is_foreign_html=True)
        assert len(docx_bytes) > 0
