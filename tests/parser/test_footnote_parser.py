"""Tests for docwow.parser.footnote_parser and footnote parsing via docx_parser."""
from pathlib import Path

import pytest

from docwow.models.footnote import Footnote
from docwow.models.paragraph import FootnoteRef, Paragraph, TextRun
from docwow.parser.docx_parser import parse_docx

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestFootnotesDocxFixture:
    """Parse tests/fixtures/footnotes.docx and verify the extracted data."""

    @pytest.fixture(scope="class")
    def doc(self):
        return parse_docx(FIXTURES / "footnotes.docx")

    def test_has_footnotes(self, doc):
        assert len(doc.footnotes) == 2

    def test_has_endnotes(self, doc):
        assert len(doc.endnotes) == 1

    def test_footnote_note_ids(self, doc):
        ids = [n.note_id for n in doc.footnotes]
        assert ids == [1, 2]

    def test_endnote_note_id(self, doc):
        assert doc.endnotes[0].note_id == 1

    def test_footnote_note_type(self, doc):
        for note in doc.footnotes:
            assert note.note_type == "footnote"

    def test_endnote_note_type(self, doc):
        assert doc.endnotes[0].note_type == "endnote"

    def test_footnote_1_text(self, doc):
        text = "".join(
            r.text for p in doc.footnotes[0].paragraphs
            for r in p.runs if isinstance(r, TextRun)
        )
        assert "footnote one" in text

    def test_footnote_2_text(self, doc):
        text = "".join(
            r.text for p in doc.footnotes[1].paragraphs
            for r in p.runs if isinstance(r, TextRun)
        )
        assert "footnote two" in text

    def test_endnote_1_text(self, doc):
        text = "".join(
            r.text for p in doc.endnotes[0].paragraphs
            for r in p.runs if isinstance(r, TextRun)
        )
        assert "endnote one" in text

    def test_footnote_paragraphs_are_paragraph_instances(self, doc):
        for note in doc.footnotes:
            for para in note.paragraphs:
                assert isinstance(para, Paragraph)

    def test_body_contains_footnote_refs(self, doc):
        all_runs = [
            run
            for item in doc.body
            if isinstance(item, Paragraph)
            for run in item.runs
        ]
        refs = [r for r in all_runs if isinstance(r, FootnoteRef)]
        assert len(refs) >= 2

    def test_body_contains_endnote_ref(self, doc):
        all_runs = [
            run
            for item in doc.body
            if isinstance(item, Paragraph)
            for run in item.runs
        ]
        refs = [r for r in all_runs if isinstance(r, FootnoteRef) and r.note_type == "endnote"]
        assert len(refs) >= 1

    def test_footnote_ref_note_ids(self, doc):
        all_runs = [
            run
            for item in doc.body
            if isinstance(item, Paragraph)
            for run in item.runs
        ]
        fn_refs = [r for r in all_runs if isinstance(r, FootnoteRef) and r.note_type == "footnote"]
        ids = sorted(r.note_id for r in fn_refs)
        assert ids == [1, 2]

    def test_separator_pseudo_notes_are_skipped(self, doc):
        all_ids = [n.note_id for n in doc.footnotes]
        assert -1 not in all_ids
        assert 0 not in all_ids


class TestEmptyDocumentHasNoFootnotes:
    def test_empty_doc_footnotes(self):
        doc = parse_docx(FIXTURES / "empty.docx")
        assert doc.footnotes == ()
        assert doc.endnotes == ()
