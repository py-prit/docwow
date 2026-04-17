"""Tests for cross-reference support via the mutable API."""

from __future__ import annotations

from pathlib import Path

import docwow
from docwow.api.paragraph import MutableParagraph
from docwow.api.run import MutableBookmark, MutableCrossRef, RunCollection
from docwow.models.paragraph import CrossRef

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestMutableCrossRef:
    def test_default_fields(self):
        ref = MutableCrossRef()
        assert ref.bookmark_name == ""
        assert ref.display_text == ""

    def test_init_with_values(self):
        ref = MutableCrossRef("MyBookmark", "Section 1")
        assert ref.bookmark_name == "MyBookmark"
        assert ref.display_text == "Section 1"

    def test_set_bookmark_name(self):
        ref = MutableCrossRef()
        result = ref.set_bookmark_name("Ref123")
        assert ref.bookmark_name == "Ref123"
        assert result is ref

    def test_set_display_text(self):
        ref = MutableCrossRef()
        result = ref.set_display_text("Chapter 2")
        assert ref.display_text == "Chapter 2"
        assert result is ref

    def test_to_frozen(self):
        ref = MutableCrossRef("Bm", "text")
        frozen = ref._to_frozen()
        assert isinstance(frozen, CrossRef)
        assert frozen.bookmark_name == "Bm"
        assert frozen.display_text == "text"


class TestRunCollectionAddCrossRef:
    def test_add_cross_ref(self):
        rc = RunCollection()
        ref = rc.add_cross_ref("Bm", "Section 1")
        assert isinstance(ref, MutableCrossRef)
        assert len(rc) == 1
        assert ref.bookmark_name == "Bm"
        assert ref.display_text == "Section 1"

    def test_add_cross_ref_no_display(self):
        rc = RunCollection()
        ref = rc.add_cross_ref("Bm")
        assert ref.display_text == ""

    def test_reject_frozen_cross_ref(self):
        import pytest
        rc = RunCollection()
        with pytest.raises(TypeError):
            rc.append(CrossRef(bookmark_name="x"))


class TestCrossRefRoundTrip:
    def test_cross_ref_survives_docx_round_trip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_bookmark("MyTarget")
        para.runs.add_text("Target text")

        para2 = list(doc.paragraphs)[1] if len(list(doc.paragraphs)) > 1 else para
        if isinstance(para2, MutableParagraph) and para2 is not para:
            para2.runs.clear()
            para2.runs.add_cross_ref("MyTarget", "See target")
        else:
            # Add a second paragraph
            doc.paragraphs.add_paragraph("")
            new_para = list(doc.paragraphs)[-1]
            if isinstance(new_para, MutableParagraph):
                new_para.runs.add_cross_ref("MyTarget", "See target")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        paras = [p for p in doc2.paragraphs if isinstance(p, MutableParagraph)]
        refs = [
            r for p in paras for r in p.runs
            if isinstance(r, MutableCrossRef)
        ]
        assert len(refs) >= 1
        assert refs[0].bookmark_name == "MyTarget"
        assert refs[0].display_text == "See target"
