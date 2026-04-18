"""Tests for API completeness additions: delete methods and find()."""

from __future__ import annotations

import pytest

from docwow.api.document import DocumentWrapper
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.toc import MutableTableOfContents, MutableTocEntry
from docwow.api.run import MutableRun


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_with_footnotes():
    doc = DocumentWrapper()
    fn1 = doc.add_footnote("footnote")
    fn1.paragraphs.add_paragraph("Footnote one")
    fn2 = doc.add_footnote("footnote")
    fn2.paragraphs.add_paragraph("Footnote two")
    para = doc.paragraphs.add_paragraph("Body text")
    para.runs.add_footnote_ref(fn1.note_id)
    para.runs.add_footnote_ref(fn2.note_id)
    return doc, fn1, fn2


def _doc_with_comments():
    doc = DocumentWrapper()
    c1 = doc.add_comment(author="Alice", text="First comment")
    c2 = doc.add_comment(author="Bob", text="Second comment")
    para = doc.paragraphs.add_paragraph("Body text")
    para.runs.add_comment_ref(c1.comment_id)
    para.runs.add_comment_ref(c2.comment_id)
    return doc, c1, c2


# ---------------------------------------------------------------------------
# remove_footnote
# ---------------------------------------------------------------------------

class TestRemoveFootnote:
    def test_removes_from_list(self):
        doc, fn1, fn2 = _doc_with_footnotes()
        doc.remove_footnote(fn1.note_id)
        assert len(doc.footnotes) == 1
        assert doc.footnotes[0].note_id == fn2.note_id

    def test_removes_refs_from_body(self):
        doc, fn1, fn2 = _doc_with_footnotes()
        doc.remove_footnote(fn1.note_id)
        from docwow.api.footnote import MutableFootnoteRef
        para = doc.paragraphs[0]
        refs = [r for r in para.runs if isinstance(r, MutableFootnoteRef)]
        assert all(r.note_id != fn1.note_id for r in refs)

    def test_raises_on_missing_id(self):
        doc, _, _ = _doc_with_footnotes()
        with pytest.raises(KeyError):
            doc.remove_footnote(999)

    def test_does_not_remove_other_footnotes(self):
        doc, fn1, fn2 = _doc_with_footnotes()
        doc.remove_footnote(fn1.note_id)
        from docwow.api.footnote import MutableFootnoteRef
        para = doc.paragraphs[0]
        refs = [r for r in para.runs if isinstance(r, MutableFootnoteRef)]
        assert any(r.note_id == fn2.note_id for r in refs)


# ---------------------------------------------------------------------------
# remove_endnote
# ---------------------------------------------------------------------------

class TestRemoveEndnote:
    def test_removes_from_endnotes_list(self):
        doc = DocumentWrapper()
        en = doc.add_footnote("endnote")
        assert len(doc.endnotes) == 1
        doc.remove_endnote(en.note_id)
        assert len(doc.endnotes) == 0

    def test_raises_on_missing_id(self):
        doc = DocumentWrapper()
        doc.add_footnote("endnote")
        with pytest.raises(KeyError):
            doc.remove_endnote(999)

    def test_does_not_touch_footnotes(self):
        doc = DocumentWrapper()
        fn = doc.add_footnote("footnote")
        en = doc.add_footnote("endnote")
        doc.remove_endnote(en.note_id)
        assert len(doc.footnotes) == 1
        assert doc.footnotes[0].note_id == fn.note_id


# ---------------------------------------------------------------------------
# remove_comment
# ---------------------------------------------------------------------------

class TestRemoveComment:
    def test_removes_from_list(self):
        doc, c1, c2 = _doc_with_comments()
        doc.remove_comment(c1.comment_id)
        assert len(doc.comments) == 1
        assert doc.comments[0].comment_id == c2.comment_id

    def test_removes_refs_from_body(self):
        doc, c1, c2 = _doc_with_comments()
        doc.remove_comment(c1.comment_id)
        from docwow.api.comment import MutableCommentRef
        para = doc.paragraphs[0]
        refs = [r for r in para.runs if isinstance(r, MutableCommentRef)]
        assert all(r.comment_id != c1.comment_id for r in refs)

    def test_raises_on_missing_id(self):
        doc, _, _ = _doc_with_comments()
        with pytest.raises(KeyError):
            doc.remove_comment(999)

    def test_does_not_remove_other_comments(self):
        doc, c1, c2 = _doc_with_comments()
        doc.remove_comment(c1.comment_id)
        from docwow.api.comment import MutableCommentRef
        para = doc.paragraphs[0]
        refs = [r for r in para.runs if isinstance(r, MutableCommentRef)]
        assert any(r.comment_id == c2.comment_id for r in refs)


# ---------------------------------------------------------------------------
# MutableTableOfContents.remove_entry / clear_entries
# ---------------------------------------------------------------------------

class TestTocRemoveEntry:
    def test_remove_entry(self):
        toc = MutableTableOfContents()
        e1 = toc.add_entry("Intro", level=1)
        e2 = toc.add_entry("Background", level=2)
        toc.remove_entry(e1)
        assert len(toc.entries) == 1
        assert toc.entries[0] is e2

    def test_remove_entry_raises_on_missing(self):
        toc = MutableTableOfContents()
        orphan = MutableTocEntry(text="Ghost")
        with pytest.raises(ValueError):
            toc.remove_entry(orphan)

    def test_clear_entries(self):
        toc = MutableTableOfContents()
        toc.add_entry("A")
        toc.add_entry("B")
        result = toc.clear_entries()
        assert len(toc.entries) == 0
        assert result is toc  # chainable


# ---------------------------------------------------------------------------
# DocumentWrapper.find()
# ---------------------------------------------------------------------------

class TestDocumentFind:
    def test_finds_matching_paragraphs(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("revenue grew by 18% this quarter")
        doc.paragraphs.add_paragraph("No match here")
        doc.paragraphs.add_paragraph("Quarterly revenue report")
        results = doc.find("revenue")
        assert len(results) == 2

    def test_returns_empty_on_no_match(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("Hello world")
        assert doc.find("xyz") == []

    def test_case_sensitive(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("Revenue")
        assert doc.find("revenue") == []
        assert len(doc.find("Revenue")) == 1

    def test_skips_tables_and_images(self):
        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("plain paragraph")
        doc.paragraphs.add_table(rows=1, cols=1)
        results = doc.find("plain")
        assert len(results) == 1
        assert isinstance(results[0], MutableParagraph)

    def test_returns_paragraph_objects(self):
        doc = DocumentWrapper()
        p = doc.paragraphs.add_paragraph("target text")
        results = doc.find("target")
        assert results[0] is p


# ---------------------------------------------------------------------------
# ParagraphCollection.find()
# ---------------------------------------------------------------------------

class TestParagraphCollectionFind:
    def test_find_returns_matching_paragraphs(self):
        col = ParagraphCollection()
        p1 = col.add_paragraph("action item: review report")
        col.add_paragraph("nothing here")
        p2 = col.add_paragraph("another action item")
        assert col.find("action item") == [p1, p2]

    def test_find_empty_on_no_match(self):
        col = ParagraphCollection()
        col.add_paragraph("hello")
        assert col.find("xyz") == []


# ---------------------------------------------------------------------------
# MutableParagraph.find() — run-level
# ---------------------------------------------------------------------------

class TestParagraphFind:
    def test_finds_runs_containing_text(self):
        para = MutableParagraph()
        para.runs.add_text("total revenue is")
        para.runs.add_text("not a match")
        para.runs.add_text("total cost")
        results = para.find("total")
        assert len(results) == 2

    def test_returns_empty_on_no_match(self):
        para = MutableParagraph()
        para.runs.add_text("hello")
        assert para.find("xyz") == []

    def test_returns_mutable_run_objects(self):
        para = MutableParagraph()
        para.runs.add_text("find me")
        results = para.find("find me")
        assert len(results) == 1
        assert isinstance(results[0], MutableRun)
