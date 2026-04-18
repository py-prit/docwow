from __future__ import annotations

from dataclasses import dataclass, field

from docwow.models.paragraph import Paragraph


@dataclass(frozen=True)
class BorderDef:
    """A single table or cell border line.

    *style* maps to the OOXML ``w:val`` attribute.  Use ``"none"`` to
    explicitly suppress a border.  *width_pt* is in points (converted to
    eighths-of-a-point for OOXML).  *color* is a 6-digit hex RGB string or
    ``None`` for the application default ("auto").
    """

    style: str = "single"       # OOXML w:val
    width_pt: float = 0.5       # pt → sz = round(width_pt * 8)
    color: str | None = None    # hex RGB, None → "auto"


@dataclass(frozen=True)
class TableBorders:
    """Per-side border configuration for a table or cell.

    ``None`` on any side means "inherit from the table default" (for cell
    borders) or "use the writer's default" (for table borders).
    ``inside_h`` and ``inside_v`` are only meaningful at the table level.
    """

    top: BorderDef | None = None
    right: BorderDef | None = None
    bottom: BorderDef | None = None
    left: BorderDef | None = None
    inside_h: BorderDef | None = None
    inside_v: BorderDef | None = None


@dataclass(frozen=True)
class TableCell:
    """A single cell in a table row."""

    paragraphs: tuple[Paragraph, ...]
    col_span: int = 1
    row_span: int = 1
    width_pt: float | None = None
    v_merge_start: bool = False
    v_merge_continue: bool = False
    shading: str | None = None
    borders: TableBorders | None = None   # None → inherit table-level borders


@dataclass(frozen=True)
class TableRow:
    """A single row in a table."""

    cells: tuple[TableCell, ...]
    height_pt: float | None = None


@dataclass(frozen=True)
class Table:
    """A Word table."""

    rows: tuple[TableRow, ...]
    width_pt: float | None = None
    col_widths_pt: tuple[float, ...] = field(default_factory=tuple)
    style_id: str | None = None
    borders: TableBorders | None = None   # None → writer default (single-line)
