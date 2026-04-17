"""Tests for the TrackedChange frozen model."""
from __future__ import annotations

from docwow.models.paragraph import TextRun, TrackedChange
from docwow.models.styles import RunFormatting


class TestTrackedChangeDefaults:
    def test_insert_type(self):
        tc = TrackedChange(change_type="insert", runs=(TextRun(text="hi"),))
        assert tc.change_type == "insert"

    def test_delete_type(self):
        tc = TrackedChange(change_type="delete", runs=(TextRun(text="bye"),))
        assert tc.change_type == "delete"

    def test_defaults(self):
        tc = TrackedChange(change_type="insert", runs=())
        assert tc.author == ""
        assert tc.date == ""
        assert tc.change_id == 0

    def test_full_fields(self):
        run = TextRun(text="added")
        tc = TrackedChange(
            change_type="insert",
            runs=(run,),
            author="Alice",
            date="2024-01-15T10:00:00Z",
            change_id=3,
        )
        assert tc.author == "Alice"
        assert tc.date == "2024-01-15T10:00:00Z"
        assert tc.change_id == 3
        assert tc.runs == (run,)

    def test_frozen(self):
        tc = TrackedChange(change_type="insert", runs=())
        import pytest
        with pytest.raises(Exception):
            tc.author = "x"  # type: ignore[misc]
