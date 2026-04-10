"""Tests for docwow.renderer.table_renderer."""
import pytest
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.models.table import Table, TableCell, TableRow
from docwow.renderer.table_renderer import render_table


def _para(text=""):
    return Paragraph(
        runs=(TextRun(text=text),) if text else (),
        formatting=ParagraphFormatting(),
    )


def _cell(text="", col_span=1, row_span=1, width_pt=None,
          v_merge_start=False, v_merge_continue=False):
    return TableCell(
        paragraphs=(_para(text),),
        col_span=col_span,
        row_span=row_span,
        width_pt=width_pt,
        v_merge_start=v_merge_start,
        v_merge_continue=v_merge_continue,
    )


def _row(*cells, height_pt=None):
    return TableRow(cells=tuple(cells), height_pt=height_pt)


def _table(*rows, style_id=None, width_pt=None, col_widths=()):
    return Table(
        rows=tuple(rows),
        style_id=style_id,
        width_pt=width_pt,
        col_widths_pt=tuple(col_widths),
    )


class TestRenderTable:
    def test_produces_table_tag(self):
        html = render_table(_table(_row(_cell())))
        assert "<table " in html
        assert "</table>" in html

    def test_dw_table_class(self):
        assert 'class="dw-table"' in render_table(_table(_row(_cell())))

    def test_border_collapse_in_style(self):
        assert "border-collapse:collapse" in render_table(_table(_row(_cell())))

    def test_style_id_attribute(self):
        t = _table(_row(_cell()), style_id="TableGrid")
        assert 'data-dw-style="TableGrid"' in render_table(t)

    def test_no_style_id_attribute_when_none(self):
        t = _table(_row(_cell()))
        assert "data-dw-style" not in render_table(t)

    def test_width_attribute(self):
        t = _table(_row(_cell()), width_pt=451.0)
        html = render_table(t)
        assert 'data-dw-width="451pt"' in html
        assert "width:451pt" in html

    def test_col_widths_attribute(self):
        t = _table(_row(_cell()), col_widths=(100.0, 150.0, 200.0))
        assert 'data-dw-col-widths="100pt,150pt,200pt"' in render_table(t)

    def test_empty_table(self):
        html = render_table(_table())
        assert "<table " in html
        assert "</table>" in html


class TestRenderRow:
    def test_produces_tr_tag(self):
        html = render_table(_table(_row(_cell())))
        assert "<tr " in html
        assert "</tr>" in html

    def test_dw_tr_class(self):
        assert 'class="dw-tr"' in render_table(_table(_row(_cell())))

    def test_height_attribute(self):
        t = _table(_row(_cell(), height_pt=28.0))
        html = render_table(t)
        assert 'data-dw-height="28pt"' in html
        assert "height:28pt" in html

    def test_no_height_attribute_when_none(self):
        t = _table(_row(_cell()))
        assert "data-dw-height" not in render_table(t)

    def test_multiple_rows(self):
        t = _table(_row(_cell("A")), _row(_cell("B")))
        html = render_table(t)
        assert html.count("<tr ") == 2


class TestRenderCell:
    def test_produces_td_tag(self):
        html = render_table(_table(_row(_cell())))
        assert "<td " in html
        assert "</td>" in html

    def test_dw_td_class(self):
        assert 'class="dw-td"' in render_table(_table(_row(_cell())))

    def test_cell_text_rendered(self):
        html = render_table(_table(_row(_cell("Hello"))))
        assert "Hello" in html

    def test_colspan_attribute(self):
        t = _table(_row(_cell(col_span=3)))
        html = render_table(t)
        assert 'colspan="3"' in html
        assert 'data-dw-col-span="3"' in html

    def test_no_colspan_when_one(self):
        t = _table(_row(_cell(col_span=1)))
        html = render_table(t)
        assert "colspan" not in html

    def test_rowspan_attribute(self):
        t = _table(_row(_cell(row_span=2)))
        html = render_table(t)
        assert 'rowspan="2"' in html
        assert 'data-dw-row-span="2"' in html

    def test_no_rowspan_when_one(self):
        t = _table(_row(_cell(row_span=1)))
        assert "rowspan" not in render_table(t)

    def test_width_attribute(self):
        t = _table(_row(_cell(width_pt=144.0)))
        html = render_table(t)
        assert 'data-dw-width="144pt"' in html
        assert "width:144pt" in html

    def test_v_merge_start_attribute(self):
        t = _table(_row(_cell(v_merge_start=True)))
        assert 'data-dw-v-merge-start="true"' in render_table(t)

    def test_v_merge_continue_attribute(self):
        t = _table(_row(_cell(v_merge_continue=True)))
        assert 'data-dw-v-merge-continue="true"' in render_table(t)

    def test_v_merge_continue_hidden(self):
        # Continuation cells should be display:none
        t = _table(_row(_cell(v_merge_continue=True)))
        assert "display:none" in render_table(t)

    def test_vertical_align_top(self):
        assert "vertical-align:top" in render_table(_table(_row(_cell())))

    def test_multiple_cells_in_row(self):
        t = _table(_row(_cell("A"), _cell("B"), _cell("C")))
        html = render_table(t)
        assert html.count("<td ") == 3
        assert "A" in html
        assert "B" in html
        assert "C" in html

    def test_empty_cell(self):
        t = _table(_row(TableCell(paragraphs=())))
        html = render_table(t)
        assert "<td " in html
