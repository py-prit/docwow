"""Tests for docwow.html_parser.table_parser."""
import lxml.html

from docwow.html_parser.table_parser import parse_table
from docwow.models.table import Table, TableCell, TableRow


def _el(html_str: str):
    return lxml.html.fragment_fromstring(html_str)


def _simple_table(cell_html="<p class='dw-p'><span class='dw-r'>text</span></p>",
                  table_attrs="", td_attrs="", tr_attrs=""):
    return _el(
        f'<table class="dw-table" {table_attrs}>'
        f'<tr class="dw-tr" {tr_attrs}>'
        f'<td class="dw-td" {td_attrs}>{cell_html}</td>'
        f'</tr>'
        f'</table>'
    )


class TestParseTable:
    def test_returns_table(self):
        assert isinstance(parse_table(_simple_table()), Table)

    def test_style_id(self):
        t = parse_table(_simple_table(table_attrs='data-dw-style="TableGrid"'))
        assert t.style_id == "TableGrid"

    def test_no_style_id_when_absent(self):
        assert parse_table(_simple_table()).style_id is None

    def test_width(self):
        t = parse_table(_simple_table(table_attrs='data-dw-width="451pt"'))
        assert t.width_pt == 451.0

    def test_no_width_when_absent(self):
        assert parse_table(_simple_table()).width_pt is None

    def test_col_widths(self):
        t = parse_table(_simple_table(table_attrs='data-dw-col-widths="100pt,150pt,200pt"'))
        assert t.col_widths_pt == (100.0, 150.0, 200.0)

    def test_empty_col_widths(self):
        assert parse_table(_simple_table()).col_widths_pt == ()

    def test_empty_table_no_rows(self):
        t = parse_table(_el('<table class="dw-table"></table>'))
        assert t.rows == ()


class TestParseRow:
    def test_returns_table_row(self):
        t = parse_table(_simple_table())
        assert isinstance(t.rows[0], TableRow)

    def test_row_height(self):
        t = parse_table(_simple_table(tr_attrs='data-dw-height="28pt"'))
        assert t.rows[0].height_pt == 28.0

    def test_no_height_when_absent(self):
        assert parse_table(_simple_table()).rows[0].height_pt is None

    def test_multiple_rows(self):
        el = _el(
            '<table class="dw-table">'
            '<tr class="dw-tr"><td class="dw-td"><p class="dw-p"></p></td></tr>'
            '<tr class="dw-tr"><td class="dw-td"><p class="dw-p"></p></td></tr>'
            '</table>'
        )
        assert len(parse_table(el).rows) == 2


class TestParseCell:
    def test_returns_table_cell(self):
        t = parse_table(_simple_table())
        assert isinstance(t.rows[0].cells[0], TableCell)

    def test_cell_text(self):
        t = parse_table(_simple_table())
        cell = t.rows[0].cells[0]
        assert len(cell.paragraphs) == 1
        assert cell.paragraphs[0].runs[0].text == "text"

    def test_col_span(self):
        t = parse_table(_simple_table(td_attrs='colspan="3" data-dw-col-span="3"'))
        assert t.rows[0].cells[0].col_span == 3

    def test_default_col_span(self):
        assert parse_table(_simple_table()).rows[0].cells[0].col_span == 1

    def test_row_span(self):
        t = parse_table(_simple_table(td_attrs='rowspan="2" data-dw-row-span="2"'))
        assert t.rows[0].cells[0].row_span == 2

    def test_default_row_span(self):
        assert parse_table(_simple_table()).rows[0].cells[0].row_span == 1

    def test_cell_width(self):
        t = parse_table(_simple_table(td_attrs='data-dw-width="144pt"'))
        assert t.rows[0].cells[0].width_pt == 144.0

    def test_no_width_when_absent(self):
        assert parse_table(_simple_table()).rows[0].cells[0].width_pt is None

    def test_v_merge_start(self):
        t = parse_table(_simple_table(td_attrs='data-dw-v-merge-start="true"'))
        assert t.rows[0].cells[0].v_merge_start is True

    def test_v_merge_continue(self):
        t = parse_table(_simple_table(td_attrs='data-dw-v-merge-continue="true"'))
        assert t.rows[0].cells[0].v_merge_continue is True

    def test_no_v_merge_by_default(self):
        cell = parse_table(_simple_table()).rows[0].cells[0]
        assert cell.v_merge_start is False
        assert cell.v_merge_continue is False

    def test_multiple_cells(self):
        el = _el(
            '<table class="dw-table"><tr class="dw-tr">'
            '<td class="dw-td"><p class="dw-p"><span class="dw-r">A</span></p></td>'
            '<td class="dw-td"><p class="dw-p"><span class="dw-r">B</span></p></td>'
            '</tr></table>'
        )
        cells = parse_table(el).rows[0].cells
        assert len(cells) == 2
        assert cells[0].paragraphs[0].runs[0].text == "A"
        assert cells[1].paragraphs[0].runs[0].text == "B"

    def test_empty_cell(self):
        el = _el('<table class="dw-table"><tr class="dw-tr"><td class="dw-td"></td></tr></table>')
        cell = parse_table(el).rows[0].cells[0]
        assert cell.paragraphs == ()
