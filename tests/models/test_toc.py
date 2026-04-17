"""Tests for docwow.models.toc — TocEntry and TableOfContents."""
from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.toc import TableOfContents, TocEntry


class TestTocEntryConstruction:
    def test_fields_stored(self):
        e = TocEntry(text="Introduction", url="#_Toc1", level=1)
        assert e.text == "Introduction"
        assert e.url == "#_Toc1"
        assert e.level == 1

    def test_empty_url(self):
        e = TocEntry(text="Foo", url="", level=2)
        assert e.url == ""

    def test_level_nine(self):
        e = TocEntry(text="Deep", url="#x", level=9)
        assert e.level == 9


class TestTocEntryImmutability:
    def test_frozen(self):
        e = TocEntry(text="x", url="", level=1)
        with pytest.raises(FrozenInstanceError):
            e.text = "y"  # type: ignore[misc]


class TestTocEntryEquality:
    def test_equal(self):
        assert TocEntry("a", "#b", 1) == TocEntry("a", "#b", 1)

    def test_not_equal_text(self):
        assert TocEntry("a", "#b", 1) != TocEntry("x", "#b", 1)

    def test_not_equal_level(self):
        assert TocEntry("a", "#b", 1) != TocEntry("a", "#b", 2)


class TestTableOfContentsConstruction:
    def test_title_and_entries(self):
        entries = (
            TocEntry(text="Intro", url="#_Toc1", level=1),
            TocEntry(text="Background", url="#_Toc2", level=2),
        )
        toc = TableOfContents(title="Contents", entries=entries)
        assert toc.title == "Contents"
        assert len(toc.entries) == 2

    def test_empty_entries(self):
        toc = TableOfContents(title="TOC", entries=())
        assert toc.entries == ()

    def test_empty_title(self):
        toc = TableOfContents(title="", entries=())
        assert toc.title == ""


class TestTableOfContentsImmutability:
    def test_frozen(self):
        toc = TableOfContents(title="x", entries=())
        with pytest.raises(FrozenInstanceError):
            toc.title = "y"  # type: ignore[misc]


class TestTableOfContentsEquality:
    def test_equal(self):
        e = TocEntry("a", "#b", 1)
        assert TableOfContents("T", (e,)) == TableOfContents("T", (e,))

    def test_not_equal_title(self):
        assert TableOfContents("A", ()) != TableOfContents("B", ())
