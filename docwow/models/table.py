from __future__ import annotations

from dataclasses import dataclass, field

from docwow.models.paragraph import Paragraph


@dataclass(frozen=True)
class TableCell:
    """A single cell in a table row."""

    paragraphs: tuple[Paragraph, ...]
    col_span: int = 1            # horizontal merge: number of grid columns this cell spans
    row_span: int = 1            # vertical merge: number of rows this cell spans
    width_pt: float | None = None
    v_merge_start: bool = False  # True when this cell is the top of a vertical merge group
    v_merge_continue: bool = False  # True when this cell is a continuation of a vertical merge
    shading: str | None = None  # hex RGB background e.g. "ED7D31"; None = none


@dataclass(frozen=True)
class TableRow:
    """A single row in a table."""

    cells: tuple[TableCell, ...]
    height_pt: float | None = None   # exact row height; None = auto


@dataclass(frozen=True)
class Table:
    """A Word table."""

    rows: tuple[TableRow, ...]
    width_pt: float | None = None
    col_widths_pt: tuple[float, ...] = field(default_factory=tuple)
    style_id: str | None = None
