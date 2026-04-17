"""Tests for MutableTrackedChange and RunCollection.add_insertion/add_deletion."""
from __future__ import annotations

import pytest

from docwow.api.run import MutableTrackedChange, RunCollection
from docwow.models.paragraph import TrackedChange, TextRun


class TestMutableTrackedChange:
    def test_insert_type(self):
        tc = MutableTrackedChange("insert", text="hello")
        assert tc.change_type == "insert"

    def test_delete_type(self):
        tc = MutableTrackedChange("delete", text="bye")
        assert tc.change_type == "delete"

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            MutableTrackedChange("update", text="x")

    def test_get_text(self):
        tc = MutableTrackedChange("insert", text="hello")
        assert tc.get_text() == "hello"

    def test_set_text_chainable(self):
        tc = MutableTrackedChange("insert", text="a")
        result = tc.set_text("b")
        assert result is tc
        assert tc.get_text() == "b"

    def test_set_author_chainable(self):
        tc = MutableTrackedChange("insert", text="x")
        result = tc.set_author("Alice")
        assert result is tc
        assert tc.author == "Alice"

    def test_set_date_chainable(self):
        tc = MutableTrackedChange("insert", text="x")
        result = tc.set_date("2024-01-15T10:00:00Z")
        assert result is tc
        assert tc.date == "2024-01-15T10:00:00Z"

    def test_to_frozen_insert(self):
        tc = MutableTrackedChange("insert", text="added", author="Bob", date="2024-01-01T00:00:00Z", change_id=3)
        frozen = tc._to_frozen()
        assert isinstance(frozen, TrackedChange)
        assert frozen.change_type == "insert"
        assert frozen.author == "Bob"
        assert frozen.date == "2024-01-01T00:00:00Z"
        assert frozen.change_id == 3
        assert len(frozen.runs) == 1
        assert isinstance(frozen.runs[0], TextRun)
        assert frozen.runs[0].text == "added"

    def test_to_frozen_delete(self):
        tc = MutableTrackedChange("delete", text="removed")
        frozen = tc._to_frozen()
        assert frozen.change_type == "delete"
        assert frozen.runs[0].text == "removed"


class TestRunCollectionFactories:
    def test_add_insertion_returns_mutable_tracked_change(self):
        rc = RunCollection()
        result = rc.add_insertion("new text", author="Alice", date="2024-01-01T00:00:00Z")
        assert isinstance(result, MutableTrackedChange)
        assert result.change_type == "insert"
        assert result.get_text() == "new text"
        assert result.author == "Alice"

    def test_add_deletion_returns_mutable_tracked_change(self):
        rc = RunCollection()
        result = rc.add_deletion("old text", author="Bob")
        assert isinstance(result, MutableTrackedChange)
        assert result.change_type == "delete"
        assert result.get_text() == "old text"

    def test_insertion_appended_to_collection(self):
        rc = RunCollection()
        rc.add_insertion("x")
        assert len(rc) == 1

    def test_deletion_appended_to_collection(self):
        rc = RunCollection()
        rc.add_deletion("y")
        assert len(rc) == 1

    def test_to_frozen_includes_tracked_changes(self):
        rc = RunCollection()
        rc.add_insertion("added", author="Alice")
        rc.add_deletion("removed", author="Bob")
        frozen = rc._to_frozen()
        assert len(frozen) == 2
        assert isinstance(frozen[0], TrackedChange)
        assert frozen[0].change_type == "insert"
        assert isinstance(frozen[1], TrackedChange)
        assert frozen[1].change_type == "delete"

    def test_cannot_add_frozen_tracked_change_directly(self):
        rc = RunCollection()
        frozen = TrackedChange(change_type="insert", runs=(TextRun(text="x"),))
        with pytest.raises(TypeError):
            rc.append(frozen)  # type: ignore[arg-type]


class TestEndToEndRoundTrip:
    def test_docx_roundtrip(self):
        """Build a doc with tracked changes, save to DOCX, parse back."""
        import io
        import docwow
        from docwow.api import DocumentWrapper

        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph()
        para.runs.add_text("Review this: ")
        para.runs.add_insertion("new idea", author="Alice", date="2024-01-15T10:00:00Z", change_id=1)
        para.runs.add_text(" and remove ")
        para.runs.add_deletion("old idea", author="Bob", date="2024-01-16T09:00:00Z", change_id=2)

        docx_bytes = doc.to_bytes()

        # Parse back
        with open("/tmp/tc_test.docx", "wb") as f:
            f.write(docx_bytes)
        restored = docwow.open("/tmp/tc_test.docx")

        restored_para = restored.paragraphs[0]
        runs = list(restored_para.runs)
        tc_runs = [r for r in runs if isinstance(r, MutableTrackedChange)]
        assert len(tc_runs) == 2
        assert tc_runs[0].change_type == "insert"
        assert tc_runs[0].get_text() == "new idea"
        assert tc_runs[0].author == "Alice"
        assert tc_runs[1].change_type == "delete"
        assert tc_runs[1].get_text() == "old idea"
        assert tc_runs[1].author == "Bob"

    def test_html_roundtrip(self):
        """Build a doc with tracked changes, render to HTML, parse back to DOCX."""
        import docwow
        from docwow.api import DocumentWrapper

        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph()
        para.runs.add_insertion("inserted", author="Alice", date="2024-01-15T10:00:00Z", change_id=1)
        para.runs.add_deletion("deleted", author="Bob", date="2024-01-16T09:00:00Z", change_id=2)

        html = doc.to_html()
        assert "dw-ins" in html
        assert "dw-del" in html
        assert "Alice" in html
        assert "Bob" in html

        docx_bytes = docwow.to_docx(html)
        with open("/tmp/tc_html_rt.docx", "wb") as f:
            f.write(docx_bytes)
        restored = docwow.open("/tmp/tc_html_rt.docx")

        runs = list(restored.paragraphs[0].runs)
        tc_runs = [r for r in runs if isinstance(r, MutableTrackedChange)]
        assert len(tc_runs) == 2
        assert tc_runs[0].change_type == "insert"
        assert tc_runs[1].change_type == "delete"
