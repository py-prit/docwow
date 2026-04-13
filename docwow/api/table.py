"""Read-only table views."""

from __future__ import annotations

from typing import Iterator

from docwow.models.paragraph import Paragraph
from docwow.models.table import Table, TableCell, TableRow


class TableCellView:
    """Read-only view over a single table cell."""

    def __init__(self, frozen: TableCell) -> None:
        self._frozen = frozen

    @property
    def col_span(self) -> int:
        return self._frozen.col_span

    @property
    def row_span(self) -> int:
        return self._frozen.row_span

    @property
    def width_pt(self) -> float | None:
        return self._frozen.width_pt

    @property
    def paragraphs(self) -> tuple[Paragraph, ...]:
        """Return the frozen paragraphs in this cell (read-only)."""
        return self._frozen.paragraphs

    def get_text(self) -> str:
        """Return the concatenated text of all runs in all paragraphs."""
        parts = []
        for para in self._frozen.paragraphs:
            for run in para.runs:
                if hasattr(run, "text"):
                    parts.append(run.text)
        return "".join(parts)

    def __repr__(self) -> str:
        return f"TableCellView(col_span={self.col_span}, row_span={self.row_span})"


class TableRowView:
    """Read-only view over a table row."""

    def __init__(self, frozen: TableRow) -> None:
        self._frozen = frozen
        self._cells = tuple(TableCellView(c) for c in frozen.cells)

    @property
    def cells(self) -> tuple[TableCellView, ...]:
        return self._cells

    @property
    def height_pt(self) -> float | None:
        return self._frozen.height_pt

    def __len__(self) -> int:
        return len(self._cells)

    def __iter__(self) -> Iterator[TableCellView]:
        return iter(self._cells)

    def __getitem__(self, index: int) -> TableCellView:
        return self._cells[index]

    def __repr__(self) -> str:
        return f"TableRowView({len(self._cells)} cells)"


class TableView:
    """Read-only view over a table.  No mutation methods are provided."""

    def __init__(self, frozen: Table) -> None:
        self._frozen = frozen
        self._rows = tuple(TableRowView(r) for r in frozen.rows)

    @property
    def rows(self) -> tuple[TableRowView, ...]:
        return self._rows

    @property
    def width_pt(self) -> float | None:
        return self._frozen.width_pt

    @property
    def style_id(self) -> str | None:
        return self._frozen.style_id

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self) -> Iterator[TableRowView]:
        return iter(self._rows)

    def __getitem__(self, index: int) -> TableRowView:
        return self._rows[index]

    def _to_frozen(self) -> Table:
        """Return the original frozen Table unchanged."""
        return self._frozen

    def __repr__(self) -> str:
        return f"TableView({len(self._rows)} rows)"
