from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo
from docwow.models.styles import ParagraphFormatting, RunFormatting


@dataclass(frozen=True)
class TextRun:
    """A contiguous run of text sharing the same character formatting."""

    text: str
    formatting: RunFormatting = field(default_factory=RunFormatting)


@dataclass(frozen=True)
class ImageRun:
    """An inline image treated as a run within a paragraph."""

    image: InlineImage
    formatting: RunFormatting = field(default_factory=RunFormatting)


@dataclass(frozen=True)
class Hyperlink:
    """An inline hyperlink wrapping one or more text runs."""

    url: str
    runs: tuple[TextRun, ...]


@dataclass(frozen=True)
class PageNumberField:
    """An inline field that inserts a dynamic page number.

    ``field_type`` is one of:

    * ``"PAGE"``         — current page number
    * ``"NUMPAGES"``     — total number of pages in the document
    * ``"SECTIONPAGES"`` — total number of pages in the current section
    """

    field_type: str
    formatting: RunFormatting = field(default_factory=RunFormatting)


# A paragraph's content is a sequence of runs.
Run: TypeAlias = TextRun | ImageRun | Hyperlink | PageNumberField


@dataclass(frozen=True)
class PageBreak:
    """An explicit page break — marks the boundary between two pages."""


@dataclass(frozen=True)
class Paragraph:
    """A Word paragraph: an ordered sequence of runs with paragraph-level formatting."""

    runs: tuple[Run, ...]
    formatting: ParagraphFormatting = field(default_factory=ParagraphFormatting)
    list_info: ListInfo | None = None   # set when this paragraph is a list item
