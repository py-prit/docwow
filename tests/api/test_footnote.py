"""Tests for docwow.api.footnote — MutableFootnote, MutableFootnoteRef."""
import pytest

from docwow.api.footnote import MutableFootnote, MutableFootnoteRef
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.run import RunCollection
from docwow.models.footnote import Footnote
from docwow.models.paragraph import FootnoteRef


class TestMutableFootnote:
    def test_default_note_type(self):
        note = MutableFootnote(note_id=1)
        assert note.note_type == "footnote"

    def test_custom_note_type(self):
        note = MutableFootnote(note_id=1, note_type="endnote")
        assert note.note_type == "endnote"

    def test_note_id(self):
        note = MutableFootnote(note_id=42)
        assert note.note_id == 42

    def test_paragraphs_default_empty(self):
        note = MutableFootnote(note_id=1)
        assert isinstance(note.paragraphs, ParagraphCollection)
        assert len(note.paragraphs) == 0

    def test_paragraphs_with_collection(self):
        coll = ParagraphCollection()
        coll.add_paragraph("Hello")
        note = MutableFootnote(note_id=1, paragraphs=coll)
        assert len(note.paragraphs) == 1

    def test_get_text_empty(self):
        note = MutableFootnote(note_id=1)
        assert note.get_text() == ""

    def test_get_text_with_content(self):
        coll = ParagraphCollection()
        coll.add_paragraph("Footnote text here")
        note = MutableFootnote(note_id=1, paragraphs=coll)
        assert "Footnote text here" in note.get_text()

    def test_get_text_multiple_paragraphs(self):
        coll = ParagraphCollection()
        coll.add_paragraph("First")
        coll.add_paragraph("Second")
        note = MutableFootnote(note_id=1, paragraphs=coll)
        text = note.get_text()
        assert "First" in text
        assert "Second" in text

    def test_to_frozen_returns_footnote(self):
        note = MutableFootnote(note_id=1)
        frozen = note._to_frozen()
        assert isinstance(frozen, Footnote)

    def test_to_frozen_note_id(self):
        note = MutableFootnote(note_id=3)
        assert note._to_frozen().note_id == 3

    def test_to_frozen_note_type(self):
        note = MutableFootnote(note_id=1, note_type="endnote")
        assert note._to_frozen().note_type == "endnote"

    def test_to_frozen_paragraphs(self):
        coll = ParagraphCollection()
        coll.add_paragraph("Content")
        note = MutableFootnote(note_id=1, paragraphs=coll)
        frozen = note._to_frozen()
        assert len(frozen.paragraphs) == 1

    def test_repr(self):
        note = MutableFootnote(note_id=5)
        r = repr(note)
        assert "5" in r
        assert "footnote" in r


class TestMutableFootnoteRef:
    def test_note_id(self):
        ref = MutableFootnoteRef(note_id=2)
        assert ref.note_id == 2

    def test_default_note_type(self):
        ref = MutableFootnoteRef(note_id=1)
        assert ref.note_type == "footnote"

    def test_endnote_type(self):
        ref = MutableFootnoteRef(note_id=1, note_type="endnote")
        assert ref.note_type == "endnote"

    def test_get_text_empty(self):
        ref = MutableFootnoteRef(note_id=1)
        assert ref.get_text() == ""

    def test_to_frozen_returns_footnote_ref(self):
        ref = MutableFootnoteRef(note_id=1)
        frozen = ref._to_frozen()
        assert isinstance(frozen, FootnoteRef)

    def test_to_frozen_note_id(self):
        ref = MutableFootnoteRef(note_id=7)
        assert ref._to_frozen().note_id == 7

    def test_to_frozen_note_type(self):
        ref = MutableFootnoteRef(note_id=1, note_type="endnote")
        assert ref._to_frozen().note_type == "endnote"

    def test_repr(self):
        ref = MutableFootnoteRef(note_id=3)
        r = repr(ref)
        assert "3" in r
        assert "footnote" in r


class TestDocumentAddFootnote:
    """Tests for DocumentWrapper.add_footnote()."""

    @pytest.fixture
    def doc(self):
        from docwow.api.document import DocumentWrapper
        return DocumentWrapper()

    def test_add_footnote_returns_mutable_footnote(self, doc):
        note = doc.add_footnote()
        assert isinstance(note, MutableFootnote)

    def test_add_footnote_auto_id_starts_at_one(self, doc):
        note = doc.add_footnote()
        assert note.note_id == 1

    def test_add_footnote_increments_id(self, doc):
        n1 = doc.add_footnote()
        n2 = doc.add_footnote()
        assert n2.note_id == 2

    def test_add_footnote_registered(self, doc):
        note = doc.add_footnote()
        assert note in doc.footnotes

    def test_add_endnote(self, doc):
        note = doc.add_footnote(note_type="endnote")
        assert note.note_type == "endnote"
        assert note in doc.endnotes

    def test_footnotes_and_endnotes_separate(self, doc):
        fn = doc.add_footnote(note_type="footnote")
        en = doc.add_footnote(note_type="endnote")
        assert fn in doc.footnotes
        assert fn not in doc.endnotes
        assert en in doc.endnotes
        assert en not in doc.footnotes

    def test_footnote_ids_independent_of_endnotes(self, doc):
        fn1 = doc.add_footnote(note_type="footnote")
        en1 = doc.add_footnote(note_type="endnote")
        fn2 = doc.add_footnote(note_type="footnote")
        assert fn1.note_id == 1
        assert en1.note_id == 1
        assert fn2.note_id == 2


class TestRunCollectionAddFootnoteRef:
    def test_add_footnote_ref_returns_ref(self):
        runs = RunCollection()
        ref = runs.add_footnote_ref(note_id=1)
        assert isinstance(ref, MutableFootnoteRef)

    def test_add_footnote_ref_appended(self):
        runs = RunCollection()
        runs.add_footnote_ref(note_id=1)
        assert len(runs) == 1

    def test_add_footnote_ref_note_id(self):
        runs = RunCollection()
        ref = runs.add_footnote_ref(note_id=5)
        assert ref.note_id == 5

    def test_add_endnote_ref(self):
        runs = RunCollection()
        ref = runs.add_footnote_ref(note_id=1, note_type="endnote")
        assert ref.note_type == "endnote"


class TestApiExports:
    def test_mutable_footnote_in_api(self):
        from docwow import api
        assert hasattr(api, "MutableFootnote")

    def test_mutable_footnote_ref_in_api(self):
        from docwow import api
        assert hasattr(api, "MutableFootnoteRef")
