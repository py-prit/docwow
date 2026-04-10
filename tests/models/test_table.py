"""Tests for docwow.models.table — TableCell, TableRow, Table."""

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.table import Table, TableCell, TableRow


# ---------------------------------------------------------------------------
# TableCell
# ---------------------------------------------------------------------------

class TestTableCellDefaults:
    def test_col_span_is_one(self, sample_cell):
        assert sample_cell.col_span == 1

    def test_row_span_is_one(self, sample_cell):
        assert sample_cell.row_span == 1

    def test_width_pt_is_none(self, sample_cell):
        assert sample_cell.width_pt is None

    def test_v_merge_start_false(self, sample_cell):
        assert sample_cell.v_merge_start is False

    def test_v_merge_continue_false(self, sample_cell):
        assert sample_cell.v_merge_continue is False


class TestTableCellParagraphs:
    def test_empty_paragraphs(self):
        cell = TableCell(paragraphs=())
        assert cell.paragraphs == ()

    def test_single_paragraph(self, sample_paragraph):
        cell = TableCell(paragraphs=(sample_paragraph,))
        assert len(cell.paragraphs) == 1
        assert cell.paragraphs[0] == sample_paragraph

    def test_multiple_paragraphs(self):
        p1 = Paragraph(runs=(TextRun(text="First"),))
        p2 = Paragraph(runs=(TextRun(text="Second"),))
        cell = TableCell(paragraphs=(p1, p2))
        assert len(cell.paragraphs) == 2
        assert cell.paragraphs[0].runs[0].text == "First"
        assert cell.paragraphs[1].runs[0].text == "Second"


class TestTableCellMerging:
    def test_col_span_greater_than_one(self, sample_paragraph):
        cell = TableCell(paragraphs=(sample_paragraph,), col_span=3)
        assert cell.col_span == 3

    def test_row_span_greater_than_one(self, sample_paragraph):
        cell = TableCell(paragraphs=(sample_paragraph,), row_span=2)
        assert cell.row_span == 2

    def test_v_merge_start(self, sample_paragraph):
        cell = TableCell(paragraphs=(sample_paragraph,), v_merge_start=True)
        assert cell.v_merge_start is True
        assert cell.v_merge_continue is False

    def test_v_merge_continue(self, sample_paragraph):
        # A continuation cell typically has no content (empty paragraphs)
        cell = TableCell(paragraphs=(), v_merge_continue=True)
        assert cell.v_merge_continue is True
        assert cell.v_merge_start is False

    def test_col_and_row_span_combined(self, sample_paragraph):
        cell = TableCell(paragraphs=(sample_paragraph,), col_span=2, row_span=3)
        assert cell.col_span == 2
        assert cell.row_span == 3


class TestTableCellWidth:
    def test_width_set(self, sample_paragraph):
        cell = TableCell(paragraphs=(sample_paragraph,), width_pt=144.0)
        assert cell.width_pt == 144.0

    def test_width_fractional(self, sample_paragraph):
        cell = TableCell(paragraphs=(sample_paragraph,), width_pt=99.5)
        assert cell.width_pt == pytest.approx(99.5)


class TestTableCellImmutability:
    def test_cannot_set_paragraphs(self, sample_cell):
        with pytest.raises(FrozenInstanceError):
            sample_cell.paragraphs = ()  # type: ignore[misc]

    def test_cannot_set_col_span(self, sample_cell):
        with pytest.raises(FrozenInstanceError):
            sample_cell.col_span = 2  # type: ignore[misc]

    def test_cannot_set_row_span(self, sample_cell):
        with pytest.raises(FrozenInstanceError):
            sample_cell.row_span = 2  # type: ignore[misc]

    def test_cannot_set_v_merge_start(self, sample_cell):
        with pytest.raises(FrozenInstanceError):
            sample_cell.v_merge_start = True  # type: ignore[misc]

    def test_cannot_set_width(self, sample_cell):
        with pytest.raises(FrozenInstanceError):
            sample_cell.width_pt = 100.0  # type: ignore[misc]


class TestTableCellEquality:
    def test_equal(self):
        c1 = TableCell(paragraphs=())
        c2 = TableCell(paragraphs=())
        assert c1 == c2

    def test_not_equal_different_col_span(self):
        assert TableCell(paragraphs=(), col_span=1) != TableCell(paragraphs=(), col_span=2)

    def test_not_equal_different_paragraphs(self):
        p1 = Paragraph(runs=(TextRun(text="A"),))
        p2 = Paragraph(runs=(TextRun(text="B"),))
        assert TableCell(paragraphs=(p1,)) != TableCell(paragraphs=(p2,))


# ---------------------------------------------------------------------------
# TableRow
# ---------------------------------------------------------------------------

class TestTableRowConstruction:
    def test_cells_stored(self, sample_cell):
        row = TableRow(cells=(sample_cell,))
        assert len(row.cells) == 1
        assert row.cells[0] == sample_cell

    def test_empty_cells(self):
        row = TableRow(cells=())
        assert row.cells == ()

    def test_multiple_cells(self, sample_paragraph):
        c1 = TableCell(paragraphs=(sample_paragraph,))
        c2 = TableCell(paragraphs=(), col_span=2)
        row = TableRow(cells=(c1, c2))
        assert len(row.cells) == 2
        assert row.cells[1].col_span == 2


class TestTableRowHeight:
    def test_height_defaults_none(self, sample_cell):
        row = TableRow(cells=(sample_cell,))
        assert row.height_pt is None

    def test_height_set(self, sample_cell):
        row = TableRow(cells=(sample_cell,), height_pt=28.35)  # 1 cm in pt
        assert row.height_pt == pytest.approx(28.35)


class TestTableRowImmutability:
    def test_cannot_set_cells(self, sample_row):
        with pytest.raises(FrozenInstanceError):
            sample_row.cells = ()  # type: ignore[misc]

    def test_cannot_set_height(self, sample_row):
        with pytest.raises(FrozenInstanceError):
            sample_row.height_pt = 50.0  # type: ignore[misc]


class TestTableRowEquality:
    def test_equal(self):
        r1 = TableRow(cells=())
        r2 = TableRow(cells=())
        assert r1 == r2

    def test_not_equal_different_height(self, sample_cell):
        r1 = TableRow(cells=(sample_cell,), height_pt=20.0)
        r2 = TableRow(cells=(sample_cell,), height_pt=30.0)
        assert r1 != r2


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

class TestTableConstruction:
    def test_rows_stored(self, sample_row):
        table = Table(rows=(sample_row,))
        assert len(table.rows) == 1
        assert table.rows[0] == sample_row

    def test_empty_rows(self):
        table = Table(rows=())
        assert table.rows == ()

    def test_multiple_rows(self, sample_cell):
        r1 = TableRow(cells=(sample_cell,))
        r2 = TableRow(cells=(sample_cell,), height_pt=20.0)
        table = Table(rows=(r1, r2))
        assert len(table.rows) == 2


class TestTableDefaults:
    def test_width_pt_none(self, sample_row):
        table = Table(rows=(sample_row,))
        assert table.width_pt is None

    def test_col_widths_empty_tuple(self, sample_row):
        table = Table(rows=(sample_row,))
        assert table.col_widths_pt == ()

    def test_style_id_none(self, sample_row):
        table = Table(rows=(sample_row,))
        assert table.style_id is None


class TestTableCustomValues:
    def test_width_pt(self, sample_row):
        table = Table(rows=(sample_row,), width_pt=451.28)
        assert table.width_pt == pytest.approx(451.28)

    def test_col_widths(self, sample_row):
        widths = (100.0, 150.0, 200.0)
        table = Table(rows=(sample_row,), col_widths_pt=widths)
        assert table.col_widths_pt == widths

    def test_style_id(self, sample_row):
        table = Table(rows=(sample_row,), style_id="TableGrid")
        assert table.style_id == "TableGrid"

    def test_each_instance_gets_independent_default_col_widths(self):
        # Empty tuples are interned by CPython (same object is fine — tuples are immutable).
        # What matters is that the default is an empty tuple, not some shared mutable container.
        t1 = Table(rows=())
        t2 = Table(rows=())
        assert t1.col_widths_pt == ()
        assert t2.col_widths_pt == ()
        # Both are immutable; no risk of accidental shared-state mutation
        assert isinstance(t1.col_widths_pt, tuple)
        assert isinstance(t2.col_widths_pt, tuple)


class TestTableImmutability:
    def test_cannot_set_rows(self, sample_table):
        with pytest.raises(FrozenInstanceError):
            sample_table.rows = ()  # type: ignore[misc]

    def test_cannot_set_width(self, sample_table):
        with pytest.raises(FrozenInstanceError):
            sample_table.width_pt = 300.0  # type: ignore[misc]

    def test_cannot_set_col_widths(self, sample_table):
        with pytest.raises(FrozenInstanceError):
            sample_table.col_widths_pt = (100.0,)  # type: ignore[misc]

    def test_cannot_set_style_id(self, sample_table):
        with pytest.raises(FrozenInstanceError):
            sample_table.style_id = "Normal"  # type: ignore[misc]


class TestTableEquality:
    def test_equal_empty(self):
        assert Table(rows=()) == Table(rows=())

    def test_not_equal_different_style(self, sample_row):
        t1 = Table(rows=(sample_row,), style_id="Grid")
        t2 = Table(rows=(sample_row,), style_id="Plain")
        assert t1 != t2


class TestTableHashable:
    def test_can_be_in_set(self, sample_table):
        s = {sample_table, sample_table}
        assert len(s) == 1
