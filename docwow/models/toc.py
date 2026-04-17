"""Frozen dataclasses for Table of Contents (TOC) support."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TocEntry:
    """A single entry in a Table of Contents.

    Attributes:
        text:  Visible label of the entry (e.g. ``"1. Introduction"``).
        url:   Internal anchor target (e.g. ``"#_Toc123456789"``), or an
               empty string when no anchor is available.
        level: Hierarchy depth, 1–9, matching Word styles TOC1–TOC9.
    """

    text: str
    url: str
    level: int


@dataclass(frozen=True)
class TableOfContents:
    """A structured document table of contents.

    In OOXML this is stored as a ``w:sdt`` (structured document tag) element
    with its content paragraphs using styles ``TOCHeading``, ``TOC1``–``TOC9``.

    Attributes:
        title:   Heading text shown above the entry list (e.g. ``"Contents"``).
        entries: Ordered sequence of :class:`TocEntry` items.
    """

    title: str
    entries: tuple[TocEntry, ...]
