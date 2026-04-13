from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from docwow.models.header_footer import HeaderFooter
from docwow.models.lists import NumberingDefinition
from docwow.models.paragraph import PageBreak, Paragraph
from docwow.models.styles import Style
from docwow.models.table import Table

# Top-level body elements
BodyElement: TypeAlias = Paragraph | Table | PageBreak


@dataclass(frozen=True)
class Document:
    """
    Root of the internal document model.

    All lengths are in points (pt).  EMU→pt conversion happens in the parser;
    pt→CSS conversion happens in the renderer.

    Default page size: A4 (595.28 × 841.89 pt).
    Default margins: 1 inch (72 pt) on all sides.
    """

    body: tuple[BodyElement, ...]
    styles: tuple[Style, ...]
    numbering: tuple[NumberingDefinition, ...]

    # Page geometry (pt)
    page_width_pt: float = 595.28    # A4 width
    page_height_pt: float = 841.89   # A4 height
    margin_top_pt: float = 72.0      # 1 inch
    margin_bottom_pt: float = 72.0
    margin_left_pt: float = 72.0
    margin_right_pt: float = 72.0

    # Headers and footers (optional)
    header_default: HeaderFooter | None = None
    header_first: HeaderFooter | None = None
    header_even: HeaderFooter | None = None
    footer_default: HeaderFooter | None = None
    footer_first: HeaderFooter | None = None
    footer_even: HeaderFooter | None = None
    title_pg: bool = False  # True → different header/footer on first page
