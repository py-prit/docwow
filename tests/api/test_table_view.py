"""Tests for TableView, TableRowView, TableCellView."""
from __future__ import annotations

import pytest

from docwow.api.table import TableCellView, TableRowView, TableView
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.models.table import Table, TableCell, TableRow


def _make_cell(text: str = "", col_span: int = 1, row_span: int = 1) -> TableCell:
    run = TextRun(text=text)
    para = Paragraph(runs=(run,))
    return TableCell(
        paragraphs=(para,),
        col_span=col_span,
        row_span=row_span,
        width_pt=100.0,
    )


def _make_table(rows: int = 2, cols: int = 2) -> Table:
    table_rows = tuple(
        TableRow(
            cells=tuple(_make_cell(f"r{r}c{c}") for c in range(cols)),
            height_pt=None,
        )
        for r in range(rows)
    )
    return Table(rows=table_rows, width_pt=400.0, style_id="TableNormal")


class TestTableCellView:
    def test_col_span(self):
        cell = TableCellView(_make_cell(col_span=2))
        assert cell.col_span == 2

    def test_row_span(self):
        cell = TableCellView(_make_cell(row_span=3))
        assert cell.row_span == 3

    def test_width_pt(self):
        cell = TableCellView(_make_cell())
        assert cell.width_pt == 100.0

    def test_paragraphs(self):
        cell = TableCellView(_make_cell("hello"))
        assert len(cell.paragraphs) == 1
        assert isinstance(cell.paragraphs[0], Paragraph)

    def test_get_text(self):
        cell = TableCellView(_make_cell("hello"))
        assert cell.get_text() == "hello"

    def test_get_text_empty(self):
        cell = TableCellView(_make_cell(""))
        assert cell.get_text() == ""

    def test_repr(self):
        cell = TableCellView(_make_cell())
        assert "TableCellView" in repr(cell)


class TestTableRowView:
    def test_cells(self):
        table = _make_table(rows=1, cols=3)
        row = TableRowView(table.rows[0])
        assert len(row.cells) == 3

    def test_height_pt(self):
        tr = TableRow(cells=(_make_cell(),), height_pt=20.0)
        row = TableRowView(tr)
        assert row.height_pt == 20.0

    def test_len(self):
        table = _make_table(rows=1, cols=2)
        row = TableRowView(table.rows[0])
        assert len(row) == 2

    def test_iter(self):
        table = _make_table(rows=1, cols=2)
        row = TableRowView(table.rows[0])
        cells = list(row)
        assert all(isinstance(c, TableCellView) for c in cells)

    def test_getitem(self):
        table = _make_table(rows=1, cols=2)
        row = TableRowView(table.rows[0])
        assert isinstance(row[0], TableCellView)

    def test_repr(self):
        table = _make_table(rows=1, cols=2)
        row = TableRowView(table.rows[0])
        assert "TableRowView" in repr(row)


class TestTableView:
    def test_rows(self):
        table = _make_table(rows=3, cols=2)
        tv = TableView(table)
        assert len(tv.rows) == 3

    def test_width_pt(self):
        table = _make_table()
        tv = TableView(table)
        assert tv.width_pt == 400.0

    def test_style_id(self):
        table = _make_table()
        tv = TableView(table)
        assert tv.style_id == "TableNormal"

    def test_len(self):
        table = _make_table(rows=2)
        tv = TableView(table)
        assert len(tv) == 2

    def test_iter(self):
        table = _make_table(rows=2)
        tv = TableView(table)
        rows = list(tv)
        assert all(isinstance(r, TableRowView) for r in rows)

    def test_getitem(self):
        table = _make_table(rows=2)
        tv = TableView(table)
        assert isinstance(tv[0], TableRowView)

    def test_cell_text_access(self):
        table = _make_table(rows=2, cols=2)
        tv = TableView(table)
        assert tv[0][0].get_text() == "r0c0"
        assert tv[1][1].get_text() == "r1c1"

    def test_repr(self):
        table = _make_table(rows=2)
        tv = TableView(table)
        assert "TableView" in repr(tv)
        assert "2" in repr(tv)


class TestTableViewToFrozen:
    def test_returns_same_frozen_table(self):
        table = _make_table()
        tv = TableView(table)
        assert tv._to_frozen() is table


class TestTableViewNoMutation:
    def test_no_append(self):
        table = _make_table()
        tv = TableView(table)
        assert not hasattr(tv, "append")

    def test_no_insert(self):
        table = _make_table()
        tv = TableView(table)
        assert not hasattr(tv, "insert")

    def test_no_remove(self):
        table = _make_table()
        tv = TableView(table)
        assert not hasattr(tv, "remove")
