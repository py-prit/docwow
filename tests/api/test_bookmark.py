"""Tests for MutableBookmark and RunCollection.add_bookmark()."""
from __future__ import annotations

import pytest

from docwow.api.run import MutableBookmark, MutableHyperlink, MutableRun, RunCollection
from docwow.models.paragraph import BookmarkStart


class TestMutableBookmarkConstruction:
    def test_default_name_is_empty(self):
        bm = MutableBookmark()
        assert bm.name == ""

    def test_name_stored(self):
        bm = MutableBookmark(name="intro")
        assert bm.name == "intro"

    def test_name_with_spaces(self):
        bm = MutableBookmark(name="my section")
        assert bm.name == "my section"


class TestMutableBookmarkSetter:
    def test_set_name_updates_name(self):
        bm = MutableBookmark(name="old")
        bm.set_name("new")
        assert bm.name == "new"

    def test_set_name_returns_self(self):
        bm = MutableBookmark(name="x")
        result = bm.set_name("y")
        assert result is bm

    def test_chaining(self):
        bm = MutableBookmark().set_name("section1")
        assert bm.name == "section1"


class TestMutableBookmarkToFrozen:
    def test_to_frozen_returns_bookmark_start(self):
        bm = MutableBookmark(name="intro")
        frozen = bm._to_frozen()
        assert isinstance(frozen, BookmarkStart)

    def test_to_frozen_preserves_name(self):
        bm = MutableBookmark(name="mysection")
        frozen = bm._to_frozen()
        assert frozen.name == "mysection"

    def test_to_frozen_empty_name(self):
        bm = MutableBookmark()
        frozen = bm._to_frozen()
        assert frozen.name == ""

    def test_round_trip_name(self):
        bm = MutableBookmark(name="chapter1")
        bm.set_name("chapter1-updated")
        frozen = bm._to_frozen()
        assert frozen.name == "chapter1-updated"


class TestMutableBookmarkRepr:
    def test_repr_contains_name(self):
        bm = MutableBookmark(name="sec1")
        assert "sec1" in repr(bm)


class TestRunCollectionAddBookmark:
    def test_add_bookmark_appends_to_collection(self):
        col = RunCollection()
        col.add_bookmark("intro")
        assert len(col) == 1

    def test_add_bookmark_returns_mutable_bookmark(self):
        col = RunCollection()
        result = col.add_bookmark("intro")
        assert isinstance(result, MutableBookmark)

    def test_add_bookmark_name_set(self):
        col = RunCollection()
        bm = col.add_bookmark("section1")
        assert bm.name == "section1"

    def test_add_bookmark_is_accessible_from_collection(self):
        col = RunCollection()
        bm = col.add_bookmark("anchor")
        assert col[0] is bm

    def test_add_multiple_bookmarks(self):
        col = RunCollection()
        col.add_bookmark("first")
        col.add_bookmark("second")
        assert len(col) == 2
        assert col[0].name == "first"
        assert col[1].name == "second"

    def test_bookmark_interleaved_with_runs(self):
        col = RunCollection()
        col.add_bookmark("start")
        col.add_text("Hello")
        col.add_bookmark("end")
        assert len(col) == 3
        assert isinstance(col[0], MutableBookmark)
        assert isinstance(col[1], MutableRun)
        assert isinstance(col[2], MutableBookmark)

    def test_to_frozen_produces_bookmark_start(self):
        col = RunCollection()
        col.add_bookmark("intro")
        frozen = col._to_frozen()
        assert len(frozen) == 1
        assert isinstance(frozen[0], BookmarkStart)
        assert frozen[0].name == "intro"

    def test_to_frozen_mixed_runs(self):
        col = RunCollection()
        col.add_bookmark("anchor")
        col.add_text("Hello")
        frozen = col._to_frozen()
        assert len(frozen) == 2
        assert isinstance(frozen[0], BookmarkStart)

    def test_append_mutable_bookmark(self):
        col = RunCollection()
        bm = MutableBookmark(name="x")
        col.append(bm)  # should not raise
        assert col[0] is bm


class TestRunCollectionTypeCheck:
    def test_cannot_add_frozen_bookmark_start(self):
        col = RunCollection()
        with pytest.raises(TypeError, match="MutableBookmark"):
            col.append(BookmarkStart(name="x"))  # type: ignore[arg-type]


class TestRunFromFrozen:
    def test_bookmark_start_produces_mutable_bookmark(self):
        from docwow.api._convert import run_from_frozen
        frozen = BookmarkStart(name="section1")
        mutable = run_from_frozen(frozen)
        assert isinstance(mutable, MutableBookmark)
        assert mutable.name == "section1"
