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


@dataclass(frozen=True)
class FootnoteRef:
    """An inline footnote or endnote reference marker.

    ``note_type`` is either ``"footnote"`` or ``"endnote"``.
    ``note_id`` is the integer ID matching an entry in
    ``Document.footnotes`` / ``Document.endnotes``.
    """

    note_id: int
    note_type: str = "footnote"


@dataclass(frozen=True)
class BookmarkStart:
    """An inline bookmark anchor.

    In OOXML a bookmark is a start/end pair; docwow models only the start
    (a point anchor) because HTML ``<a id="…">`` has no concept of a range.
    The matching ``w:bookmarkEnd`` is synthesised automatically on write.
    """

    name: str


@dataclass(frozen=True)
class CommentRef:
    """An inline comment reference marker.

    ``comment_id`` matches the ``w:id`` of the corresponding
    :class:`~docwow.models.comment.Comment` stored in
    ``Document.comments``.
    """

    comment_id: int


@dataclass(frozen=True)
class TrackedChange:
    """An inline tracked change (insertion or deletion).

    Represents a ``w:ins`` (insertion) or ``w:del`` (deletion) element from
    Word's track-changes feature.  ``change_type`` is either ``"insert"`` or
    ``"delete"``.  The inner ``runs`` hold the affected text; for deletions
    these were parsed from ``w:delText`` elements.
    """

    change_type: str                          # "insert" or "delete"
    runs: tuple[TextRun | ImageRun, ...]
    author: str = ""
    date: str = ""
    change_id: int = 0


# A paragraph's content is a sequence of runs.
Run: TypeAlias = TextRun | ImageRun | Hyperlink | PageNumberField | FootnoteRef | BookmarkStart | CommentRef | TrackedChange


@dataclass(frozen=True)
class PageBreak:
    """An explicit page break — marks the boundary between two pages."""


@dataclass(frozen=True)
class Paragraph:
    """A Word paragraph: an ordered sequence of runs with paragraph-level formatting."""

    runs: tuple[Run, ...]
    formatting: ParagraphFormatting = field(default_factory=ParagraphFormatting)
    list_info: ListInfo | None = None   # set when this paragraph is a list item
