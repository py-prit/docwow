"""Tests for MutableTable, MutableTableRow, MutableTableCell (and backward-compat aliases)."""
from __future__ import annotations

import pytest

from docwow.api.table import (
    MutableTable,
    MutableTableCell,
    MutableTableRow,
    TableCellView,
    TableRowView,
    TableView,
)
from docwow.api.paragraph import MutableParagraph, ParagraphCollection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cell(text: str = "", col_span: int = 1, row_span: int = 1) -> MutableTableCell:
    cell = MutableTableCell(col_span=col_span, row_span=row_span, width_pt=100.0)
    if text:
        cell.paragraphs.add_paragraph(text)
    return cell


def _make_table(rows: int = 2, cols: int = 2) -> MutableTable:
    table_rows = [
        MutableTableRow(cells=[_make_cell(f"r{r}c{c}") for c in range(cols)])
        for r in range(rows)
    ]
    return MutableTable(rows=table_rows, width_pt=400.0, style_id="TableNormal")


# ---------------------------------------------------------------------------
# MutableTableCell
# ---------------------------------------------------------------------------

class TestMutableTableCell:
    def test_col_span_default(self):
        cell = MutableTableCell()
        assert cell.col_span == 1

    def test_col_span_set(self):
        cell = _make_cell(col_span=2)
        assert cell.col_span == 2

    def test_set_col_span(self):
        cell = MutableTableCell()
        result = cell.set_col_span(3)
        assert cell.col_span == 3
        assert result is cell  # chainable

    def test_row_span_default(self):
        cell = MutableTableCell()
        assert cell.row_span == 1

    def test_row_span_set(self):
        cell = _make_cell(row_span=3)
        assert cell.row_span == 3

    def test_set_row_span(self):
        cell = MutableTableCell()
        result = cell.set_row_span(2)
        assert cell.row_span == 2
        assert result is cell

    def test_width_pt_none_by_default(self):
        cell = MutableTableCell()
        assert cell.width_pt is None

    def test_width_pt_set_at_init(self):
        cell = MutableTableCell(width_pt=120.0)
        assert cell.width_pt == 120.0

    def test_set_width_pt(self):
        cell = MutableTableCell()
        result = cell.set_width_pt(75.0)
        assert cell.width_pt == 75.0
        assert result is cell

    def test_paragraphs_is_paragraph_collection(self):
        cell = MutableTableCell()
        assert isinstance(cell.paragraphs, ParagraphCollection)

    def test_paragraphs_empty_by_default(self):
        cell = MutableTableCell()
        assert len(cell.paragraphs) == 0

    def test_get_text_empty(self):
        cell = MutableTableCell()
        assert cell.get_text() == ""

    def test_get_text_with_content(self):
        cell = _make_cell("hello")
        assert cell.get_text() == "hello"

    def test_get_text_multiple_paragraphs(self):
        cell = MutableTableCell()
        cell.paragraphs.add_paragraph("foo")
        cell.paragraphs.add_paragraph("bar")
        assert cell.get_text() == "foobar"

    def test_add_paragraph_via_paragraphs(self):
        cell = MutableTableCell()
        para = cell.paragraphs.add_paragraph("content")
        assert isinstance(para, MutableParagraph)
        assert cell.get_text() == "content"

    def test_v_merge_defaults(self):
        cell = MutableTableCell()
        assert cell.v_merge_start is False
        assert cell.v_merge_continue is False

    def test_v_merge_set_at_init(self):
        cell = MutableTableCell(v_merge_start=True)
        assert cell.v_merge_start is True

    def test_to_frozen(self):
        cell = _make_cell("text", col_span=2, row_span=1)
        frozen = cell._to_frozen()
        assert frozen.col_span == 2
        assert frozen.row_span == 1
        assert frozen.width_pt == 100.0
        assert len(frozen.paragraphs) == 1

    def test_repr(self):
        cell = MutableTableCell()
        assert "MutableTableCell" in repr(cell)


# ---------------------------------------------------------------------------
# MutableTableRow
# ---------------------------------------------------------------------------

class TestMutableTableRow:
    def test_empty_by_default(self):
        row = MutableTableRow()
        assert len(row) == 0

    def test_cells_at_init(self):
        row = MutableTableRow(cells=[_make_cell(), _make_cell()])
        assert len(row) == 2

    def test_height_pt_none_by_default(self):
        row = MutableTableRow()
        assert row.height_pt is None

    def test_height_pt_set_at_init(self):
        row = MutableTableRow(height_pt=20.0)
        assert row.height_pt == 20.0

    def test_set_height_pt(self):
        row = MutableTableRow()
        result = row.set_height_pt(15.0)
        assert row.height_pt == 15.0
        assert result is row

    def test_len(self):
        row = MutableTableRow(cells=[_make_cell(), _make_cell()])
        assert len(row) == 2

    def test_iter(self):
        row = MutableTableRow(cells=[_make_cell("a"), _make_cell("b")])
        texts = [c.get_text() for c in row]
        assert texts == ["a", "b"]

    def test_getitem(self):
        c = _make_cell("x")
        row = MutableTableRow(cells=[c])
        assert row[0] is c

    def test_append(self):
        row = MutableTableRow()
        cell = _make_cell("new")
        row.append(cell)
        assert len(row) == 1
        assert row[0] is cell

    def test_insert(self):
        row = MutableTableRow(cells=[_make_cell("a"), _make_cell("c")])
        row.insert(1, _make_cell("b"))
        assert [c.get_text() for c in row] == ["a", "b", "c"]

    def test_remove(self):
        row = MutableTableRow(cells=[_make_cell("a"), _make_cell("b")])
        row.remove(0)
        assert len(row) == 1
        assert row[0].get_text() == "b"

    def test_add_cell(self):
        row = MutableTableRow()
        cell = row.add_cell(width_pt=50.0)
        assert isinstance(cell, MutableTableCell)
        assert len(row) == 1
        assert cell.width_pt == 50.0

    def test_add_cell_returns_cell(self):
        row = MutableTableRow()
        cell = row.add_cell()
        assert row[0] is cell

    def test_append_wrong_type_raises(self):
        row = MutableTableRow()
        with pytest.raises(TypeError, match="MutableTableCell"):
            row.append("not a cell")  # type: ignore[arg-type]

    def test_to_frozen(self):
        row = MutableTableRow(cells=[_make_cell("a"), _make_cell("b")], height_pt=12.0)
        frozen = row._to_frozen()
        assert len(frozen.cells) == 2
        assert frozen.height_pt == 12.0

    def test_repr(self):
        row = MutableTableRow(cells=[_make_cell()])
        assert "MutableTableRow" in repr(row)
        assert "1" in repr(row)


# ---------------------------------------------------------------------------
# MutableTable
# ---------------------------------------------------------------------------

class TestMutableTable:
    def test_empty_by_default(self):
        table = MutableTable()
        assert len(table) == 0

    def test_rows_at_init(self):
        table = _make_table(rows=3, cols=2)
        assert len(table) == 3

    def test_width_pt_none_by_default(self):
        table = MutableTable()
        assert table.width_pt is None

    def test_width_pt_at_init(self):
        table = MutableTable(width_pt=400.0)
        assert table.width_pt == 400.0

    def test_set_width_pt(self):
        table = MutableTable()
        result = table.set_width_pt(300.0)
        assert table.width_pt == 300.0
        assert result is table

    def test_style_id_none_by_default(self):
        table = MutableTable()
        assert table.style_id is None

    def test_style_id_at_init(self):
        table = MutableTable(style_id="TableGrid")
        assert table.style_id == "TableGrid"

    def test_set_style(self):
        table = MutableTable()
        result = table.set_style("TableNormal")
        assert table.style_id == "TableNormal"
        assert result is table

    def test_col_widths_pt_empty_by_default(self):
        table = MutableTable()
        assert table.col_widths_pt == ()

    def test_set_col_widths_pt(self):
        table = MutableTable()
        result = table.set_col_widths_pt([100.0, 200.0])
        assert table.col_widths_pt == (100.0, 200.0)
        assert result is table

    def test_len(self):
        table = _make_table(rows=2)
        assert len(table) == 2

    def test_iter(self):
        table = _make_table(rows=2)
        rows = list(table)
        assert all(isinstance(r, MutableTableRow) for r in rows)

    def test_getitem(self):
        table = _make_table(rows=2)
        assert isinstance(table[0], MutableTableRow)

    def test_cell_text_access(self):
        table = _make_table(rows=2, cols=2)
        assert table[0][0].get_text() == "r0c0"
        assert table[1][1].get_text() == "r1c1"

    def test_append_row(self):
        table = MutableTable()
        row = MutableTableRow()
        table.append(row)
        assert len(table) == 1
        assert table[0] is row

    def test_insert_row(self):
        table = _make_table(rows=2, cols=1)
        new_row = MutableTableRow(cells=[_make_cell("mid")])
        table.insert(1, new_row)
        assert len(table) == 3
        assert table[1][0].get_text() == "mid"

    def test_remove_row(self):
        table = _make_table(rows=3, cols=1)
        table.remove(1)
        assert len(table) == 2

    def test_add_row(self):
        table = MutableTable()
        row = table.add_row(num_cells=3)
        assert isinstance(row, MutableTableRow)
        assert len(table) == 1
        assert len(row) == 3

    def test_add_row_with_cell_width(self):
        table = MutableTable()
        row = table.add_row(num_cells=2, cell_width_pt=100.0)
        assert row[0].width_pt == 100.0
        assert row[1].width_pt == 100.0

    def test_add_row_with_height(self):
        table = MutableTable()
        row = table.add_row(num_cells=1, height_pt=20.0)
        assert row.height_pt == 20.0

    def test_append_wrong_type_raises(self):
        table = MutableTable()
        with pytest.raises(TypeError, match="MutableTableRow"):
            table.append("not a row")  # type: ignore[arg-type]

    def test_to_frozen(self):
        table = _make_table(rows=2, cols=2)
        from docwow.models.table import Table
        frozen = table._to_frozen()
        assert isinstance(frozen, Table)
        assert len(frozen.rows) == 2
        assert frozen.width_pt == 400.0
        assert frozen.style_id == "TableNormal"

    def test_to_frozen_preserves_cell_text(self):
        table = _make_table(rows=1, cols=2)
        frozen = table._to_frozen()
        cell_text = frozen.rows[0].cells[0].paragraphs[0].runs[0].text
        assert cell_text == "r0c0"

    def test_repr(self):
        table = _make_table(rows=2)
        assert "MutableTable" in repr(table)
        assert "2" in repr(table)


# ---------------------------------------------------------------------------
# Mutation scenarios (realistic use)
# ---------------------------------------------------------------------------

class TestMutableTableEditing:
    def test_edit_cell_text(self):
        table = _make_table(rows=1, cols=1)
        cell = table[0][0]
        cell.paragraphs[0].set_text("Updated")
        assert cell.get_text() == "Updated"

    def test_add_paragraph_to_cell(self):
        table = MutableTable()
        row = table.add_row(num_cells=1)
        cell = row[0]
        cell.paragraphs.add_paragraph("Line 1")
        cell.paragraphs.add_paragraph("Line 2")
        assert cell.get_text() == "Line 1Line 2"

    def test_add_row_and_fill(self):
        table = MutableTable()
        row = table.add_row(num_cells=2)
        row[0].paragraphs.add_paragraph("Name")
        row[1].paragraphs.add_paragraph("Value")
        assert table[0][0].get_text() == "Name"
        assert table[0][1].get_text() == "Value"

    def test_round_trip_via_to_frozen(self):
        table = MutableTable(style_id="TableGrid", width_pt=500.0)
        table.set_col_widths_pt([250.0, 250.0])
        row = table.add_row(num_cells=2)
        row[0].paragraphs.add_paragraph("Header A")
        row[1].paragraphs.add_paragraph("Header B")

        frozen = table._to_frozen()
        assert frozen.style_id == "TableGrid"
        assert frozen.width_pt == 500.0
        assert frozen.col_widths_pt == (250.0, 250.0)
        assert frozen.rows[0].cells[0].paragraphs[0].runs[0].text == "Header A"
        assert frozen.rows[0].cells[1].paragraphs[0].runs[0].text == "Header B"

    def test_build_table_and_save_to_docx(self):
        """Full pipeline: build table → DocumentWrapper → DOCX bytes."""
        import docwow
        from docwow.api import DocumentWrapper

        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("Before table")

        table = doc.paragraphs.add_table(rows=2, cols=2, style_id="TableGrid")
        table[0][0].paragraphs.add_paragraph("R1C1")
        table[0][1].paragraphs.add_paragraph("R1C2")
        table[1][0].paragraphs.add_paragraph("R2C1")
        table[1][1].paragraphs.add_paragraph("R2C2")

        doc.paragraphs.add_paragraph("After table")

        data = doc.to_bytes()
        assert isinstance(data, bytes)
        assert len(data) > 0

        # Round-trip: open the saved bytes and verify table content
        reopened = docwow.open(data)
        # Find the table in body
        from docwow.api import MutableTable
        tables = [item for item in reopened.paragraphs if isinstance(item, MutableTable)]
        assert len(tables) == 1
        t = tables[0]
        assert t[0][0].get_text() == "R1C1"
        assert t[0][1].get_text() == "R1C2"
        assert t[1][0].get_text() == "R2C1"
        assert t[1][1].get_text() == "R2C2"


# ---------------------------------------------------------------------------
# Backward-compatibility aliases
# ---------------------------------------------------------------------------

class TestBackwardCompatAliases:
    def test_table_view_is_mutable_table(self):
        assert TableView is MutableTable

    def test_table_row_view_is_mutable_table_row(self):
        assert TableRowView is MutableTableRow

    def test_table_cell_view_is_mutable_table_cell(self):
        assert TableCellView is MutableTableCell
