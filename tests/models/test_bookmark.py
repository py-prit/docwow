"""Tests for docwow.models.paragraph.BookmarkStart."""
from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.paragraph import BookmarkStart, Paragraph, TextRun


class TestBookmarkStartConstruction:
    def test_name_stored(self):
        bm = BookmarkStart(name="section1")
        assert bm.name == "section1"

    def test_empty_name(self):
        bm = BookmarkStart(name="")
        assert bm.name == ""

    def test_unicode_name(self):
        bm = BookmarkStart(name="héros")
        assert bm.name == "héros"

    def test_name_with_spaces(self):
        bm = BookmarkStart(name="my section")
        assert bm.name == "my section"


class TestBookmarkStartImmutability:
    def test_name_is_frozen(self):
        bm = BookmarkStart(name="x")
        with pytest.raises(FrozenInstanceError):
            bm.name = "y"  # type: ignore[misc]


class TestBookmarkStartEquality:
    def test_equal_same_name(self):
        assert BookmarkStart(name="a") == BookmarkStart(name="a")

    def test_not_equal_different_name(self):
        assert BookmarkStart(name="a") != BookmarkStart(name="b")

    def test_not_equal_to_other_types(self):
        assert BookmarkStart(name="a") != TextRun(text="a")


class TestBookmarkStartInParagraph:
    def test_bookmark_can_be_in_paragraph_runs(self):
        bm = BookmarkStart(name="intro")
        text = TextRun(text="Introduction")
        para = Paragraph(runs=(bm, text))
        assert para.runs[0] is bm
        assert para.runs[1] is text

    def test_paragraph_with_bookmark_only(self):
        bm = BookmarkStart(name="anchor")
        para = Paragraph(runs=(bm,))
        assert len(para.runs) == 1
