from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BorderDef:
    """A single border line (table, cell, or paragraph).

    *style* maps to the OOXML ``w:val`` attribute.  Use ``"none"`` to
    explicitly suppress a border.  *width_pt* is in points (converted to
    eighths-of-a-point for OOXML).  *color* is a 6-digit hex RGB string or
    ``None`` for the application default ("auto").
    """

    style: str = "single"       # OOXML w:val
    width_pt: float = 0.5       # pt → sz = round(width_pt * 8)
    color: str | None = None    # hex RGB, None → "auto"
