"""Mutable table wrappers."""

from __future__ import annotations

from typing import Iterator

from docwow.models.table import Table, TableCell, TableRow


class MutableTableCell:
    """A mutable table cell containing an ordered sequence of paragraphs."""

    def __init__(
        self,
        paragraphs: "ParagraphCollection | None" = None,
        col_span: int = 1,
        row_span: int = 1,
        width_pt: float | None = None,
        v_merge_start: bool = False,
        v_merge_continue: bool = False,
        shading: str | None = None,
    ) -> None:
        from docwow.api.paragraph import ParagraphCollection
        self._paragraphs = paragraphs if paragraphs is not None else ParagraphCollection()
        self._col_span = col_span
        self._row_span = row_span
        self._width_pt = width_pt
        self._v_merge_start = v_merge_start
        self._v_merge_continue = v_merge_continue
        self._shading = shading

    # ---- Content access ------------------------------------------------------

    @property
    def paragraphs(self) -> "ParagraphCollection":
        """The mutable paragraph collection for this cell."""
        return self._paragraphs

    def get_text(self) -> str:
        """Return the concatenated text of all runs in all paragraphs."""
        from docwow.api.paragraph import MutableParagraph
        parts = []
        for item in self._paragraphs:
            if isinstance(item, MutableParagraph):
                parts.append(item.get_text())
        return "".join(parts)

    # ---- Span / dimension ----------------------------------------------------

    @property
    def col_span(self) -> int:
        """Number of grid columns this cell spans (default 1)."""
        return self._col_span

    def set_col_span(self, value: int) -> "MutableTableCell":
        """Set the column span."""
        self._col_span = value
        return self

    @property
    def row_span(self) -> int:
        """Number of rows this cell spans (default 1)."""
        return self._row_span

    def set_row_span(self, value: int) -> "MutableTableCell":
        """Set the row span."""
        self._row_span = value
        return self

    @property
    def width_pt(self) -> float | None:
        """Cell width in points, or None for automatic."""
        return self._width_pt

    def set_width_pt(self, width_pt: float | None) -> "MutableTableCell":
        """Set the cell width in points."""
        self._width_pt = width_pt
        return self

    # ---- Vertical merge (pass-through from parser, not user-settable) --------

    @property
    def v_merge_start(self) -> bool:
        """True if this cell begins a vertical merge group (OOXML ``w:vMerge w:val="restart"``)."""
        return self._v_merge_start

    @property
    def v_merge_continue(self) -> bool:
        """True if this cell continues a vertical merge (visually spanned by the cell above)."""
        return self._v_merge_continue

    @property
    def shading(self) -> str | None:
        """Cell background shading color as a 6-digit hex RGB string (e.g. ``'ED7D31'``), or ``None``."""
        return self._shading

    def set_shading(self, hex_rgb: str | None) -> "MutableTableCell":
        """Set the cell background shading color (6-digit hex RGB, e.g. ``'ED7D31'``) or ``None`` to clear."""
        self._shading = hex_rgb.upper() if hex_rgb else None
        return self

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> TableCell:
        """Convert to a frozen TableCell for pipeline use."""
        from docwow.models.paragraph import Paragraph, PageBreak
        frozen_paras: list[Paragraph] = []
        for item in self._paragraphs:
            if isinstance(item, PageBreak):
                continue  # skip page breaks inside cells
            frozen_paras.append(item._to_frozen())
        return TableCell(
            paragraphs=tuple(frozen_paras),
            col_span=self._col_span,
            row_span=self._row_span,
            width_pt=self._width_pt,
            v_merge_start=self._v_merge_start,
            v_merge_continue=self._v_merge_continue,
            shading=self._shading,
        )

    def __repr__(self) -> str:
        return (
            f"MutableTableCell(col_span={self._col_span}, row_span={self._row_span}, "
            f"paragraphs={len(self._paragraphs)})"
        )


class MutableTableRow:
    """A mutable table row containing an ordered sequence of cells."""

    def __init__(
        self,
        cells: list[MutableTableCell] | None = None,
        height_pt: float | None = None,
    ) -> None:
        self._cells: list[MutableTableCell] = list(cells) if cells is not None else []
        self._height_pt = height_pt

    # ---- Sequence protocol ---------------------------------------------------

    def __len__(self) -> int:
        return len(self._cells)

    def __iter__(self) -> Iterator[MutableTableCell]:
        return iter(self._cells)

    def __getitem__(self, index: int) -> MutableTableCell:
        return self._cells[index]

    # ---- Mutation ------------------------------------------------------------

    def append(self, cell: MutableTableCell) -> None:
        """Append a cell to the end of the row."""
        self._check_type(cell)
        self._cells.append(cell)

    def insert(self, index: int, cell: MutableTableCell) -> None:
        """Insert a cell at the given index."""
        self._check_type(cell)
        self._cells.insert(index, cell)

    def remove(self, index: int) -> None:
        """Remove the cell at the given index."""
        del self._cells[index]

    def add_cell(self, width_pt: float | None = None) -> MutableTableCell:
        """Create and append a new empty cell, returning it."""
        cell = MutableTableCell(width_pt=width_pt)
        self._cells.append(cell)
        return cell

    # ---- Row properties ------------------------------------------------------

    @property
    def height_pt(self) -> float | None:
        """Row height in points, or None for automatic."""
        return self._height_pt

    def set_height_pt(self, height_pt: float | None) -> "MutableTableRow":
        """Set the row height in points."""
        self._height_pt = height_pt
        return self

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> TableRow:
        """Convert to a frozen TableRow for pipeline use."""
        return TableRow(
            cells=tuple(c._to_frozen() for c in self._cells),
            height_pt=self._height_pt,
        )

    def _check_type(self, cell: object) -> None:
        if not isinstance(cell, MutableTableCell):
            raise TypeError(
                f"Expected MutableTableCell; got {type(cell).__name__!r}"
            )

    def __repr__(self) -> str:
        return f"MutableTableRow({len(self._cells)} cells)"


class MutableTable:
    """A mutable table with rows, cells, and paragraph content."""

    def __init__(
        self,
        rows: list[MutableTableRow] | None = None,
        width_pt: float | None = None,
        style_id: str | None = None,
        col_widths_pt: tuple[float, ...] = (),
    ) -> None:
        self._rows: list[MutableTableRow] = list(rows) if rows is not None else []
        self._width_pt = width_pt
        self._style_id = style_id
        self._col_widths_pt = tuple(col_widths_pt)

    # ---- Sequence protocol ---------------------------------------------------

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self) -> Iterator[MutableTableRow]:
        return iter(self._rows)

    def __getitem__(self, index: int) -> MutableTableRow:
        return self._rows[index]

    # ---- Mutation ------------------------------------------------------------

    def append(self, row: MutableTableRow) -> None:
        """Append a row to the table."""
        self._check_type(row)
        self._rows.append(row)

    def insert(self, index: int, row: MutableTableRow) -> None:
        """Insert a row at the given index."""
        self._check_type(row)
        self._rows.insert(index, row)

    def remove(self, index: int) -> None:
        """Remove the row at the given index."""
        del self._rows[index]

    def add_row(
        self,
        num_cells: int = 0,
        height_pt: float | None = None,
        cell_width_pt: float | None = None,
    ) -> MutableTableRow:
        """Create and append a new row with *num_cells* empty cells, returning it.

        Args:
            num_cells: Number of empty cells to create in the row.
            height_pt: Optional row height in points.
            cell_width_pt: Optional width to assign to each new cell.
        """
        cells = [MutableTableCell(width_pt=cell_width_pt) for _ in range(num_cells)]
        row = MutableTableRow(cells=cells, height_pt=height_pt)
        self._rows.append(row)
        return row

    # ---- Table properties ----------------------------------------------------

    @property
    def width_pt(self) -> float | None:
        """Total table width in points, or None for automatic."""
        return self._width_pt

    def set_width_pt(self, width_pt: float | None) -> "MutableTable":
        """Set the total table width in points."""
        self._width_pt = width_pt
        return self

    @property
    def style_id(self) -> str | None:
        """Word table style ID (e.g. ``'TableGrid'``, ``'TableNormal'``)."""
        return self._style_id

    def set_style(self, style_id: str | None) -> "MutableTable":
        """Set the table style by style ID."""
        self._style_id = style_id
        return self

    @property
    def col_widths_pt(self) -> tuple[float, ...]:
        """Column widths in points (may be empty if not set)."""
        return self._col_widths_pt

    def set_col_widths_pt(self, widths: tuple[float, ...] | list[float]) -> "MutableTable":
        """Set the column widths in points."""
        self._col_widths_pt = tuple(widths)
        return self

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> Table:
        """Convert to a frozen Table for pipeline use."""
        return Table(
            rows=tuple(r._to_frozen() for r in self._rows),
            width_pt=self._width_pt,
            style_id=self._style_id,
            col_widths_pt=self._col_widths_pt,
        )

    def _check_type(self, row: object) -> None:
        if not isinstance(row, MutableTableRow):
            raise TypeError(
                f"Expected MutableTableRow; got {type(row).__name__!r}"
            )

    def __repr__(self) -> str:
        return f"MutableTable({len(self._rows)} rows)"


# ---------------------------------------------------------------------------
# Backward-compatibility aliases (deprecated names kept for existing code)
# ---------------------------------------------------------------------------

TableView = MutableTable
TableRowView = MutableTableRow
TableCellView = MutableTableCell
