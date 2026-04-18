from __future__ import annotations

from dataclasses import dataclass, field
from docwow.models.borders import BorderDef


@dataclass(frozen=True)
class TabStop:
    """A single tab stop definition from w:tabs/w:tab."""

    position_pt: float
    alignment: str        # "left" | "right" | "center" | "decimal" | "bar"
    leader: str | None = None  # "dot" | "hyphen" | "underscore" | None


@dataclass(frozen=True)
class ParagraphBorders:
    """Per-side border lines on a paragraph (w:pBdr)."""

    top: BorderDef | None = None
    left: BorderDef | None = None
    bottom: BorderDef | None = None
    right: BorderDef | None = None


@dataclass(frozen=True)
class RunFormatting:
    """Character-level formatting for a run of text."""

    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    small_caps: bool = False
    all_caps: bool = False
    font_name: str | None = None
    font_size_pt: float | None = None  # points; converted from half-points at parse time
    color: str | None = None           # hex RGB e.g. "FF0000"; None = auto
    highlight: str | None = None       # Word highlight color name e.g. "yellow"
    vertical_align: str | None = None  # "superscript" | "subscript" | None
    char_style_id: str | None = None   # character style ID e.g. "Strong", "Emphasis"


@dataclass(frozen=True)
class ParagraphFormatting:
    """Paragraph-level formatting."""

    style_id: str | None = None
    alignment: str | None = None        # "left" | "center" | "right" | "justify" | None
    indent_left_pt: float = 0.0
    indent_right_pt: float = 0.0
    indent_first_line_pt: float = 0.0  # negative = hanging indent
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0
    line_spacing_pt: float | None = None  # None = single/auto
    keep_together: bool = False
    keep_with_next: bool = False
    page_break_before: bool = False
    shading: str | None = None          # hex RGB background e.g. "4472C4"; None = none
    tab_stops: tuple[TabStop, ...] = ()  # custom tab stop definitions
    borders: ParagraphBorders | None = None  # w:pBdr; None = no borders


@dataclass(frozen=True)
class Style:
    """A named Word style definition (paragraph, character, table, or numbering)."""

    style_id: str
    name: str
    style_type: str                          # "paragraph" | "character" | "table" | "numbering"
    based_on: str | None = None              # style_id of parent style
    paragraph_fmt: ParagraphFormatting | None = None
    run_fmt: RunFormatting | None = None
