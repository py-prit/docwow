"""Tests for small-caps and all-caps support via the mutable API."""

from __future__ import annotations

from pathlib import Path

import docwow
from docwow.api.run import MutableRun, RunCollection
from docwow.api.paragraph import MutableParagraph
from docwow.models.styles import RunFormatting

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestMutableRunSmallCaps:
    def test_default_small_caps_false(self):
        assert MutableRun("hello").small_caps is False

    def test_set_small_caps(self):
        run = MutableRun("hello")
        result = run.set_small_caps()
        assert run.small_caps is True
        assert result is run

    def test_set_small_caps_false_clears(self):
        run = MutableRun("hello")
        run.set_small_caps()
        run.set_small_caps(False)
        assert run.small_caps is False

    def test_init_with_small_caps(self):
        run = MutableRun("hello", small_caps=True)
        assert run.small_caps is True

    def test_to_frozen_carries_small_caps(self):
        run = MutableRun("hello", small_caps=True)
        assert run._to_frozen().formatting.small_caps is True

    def test_to_frozen_no_small_caps(self):
        assert MutableRun("hello")._to_frozen().formatting.small_caps is False


class TestMutableRunAllCaps:
    def test_default_all_caps_false(self):
        assert MutableRun("hello").all_caps is False

    def test_set_all_caps(self):
        run = MutableRun("hello")
        result = run.set_all_caps()
        assert run.all_caps is True
        assert result is run

    def test_set_all_caps_false_clears(self):
        run = MutableRun("hello")
        run.set_all_caps()
        run.set_all_caps(False)
        assert run.all_caps is False

    def test_init_with_all_caps(self):
        run = MutableRun("hello", all_caps=True)
        assert run.all_caps is True

    def test_to_frozen_carries_all_caps(self):
        run = MutableRun("hello", all_caps=True)
        assert run._to_frozen().formatting.all_caps is True

    def test_to_frozen_no_all_caps(self):
        assert MutableRun("hello")._to_frozen().formatting.all_caps is False


class TestRunCollectionAddText:
    def test_add_text_with_small_caps(self):
        rc = RunCollection()
        run = rc.add_text("hello", small_caps=True)
        assert run.small_caps is True

    def test_add_text_with_all_caps(self):
        rc = RunCollection()
        run = rc.add_text("hello", all_caps=True)
        assert run.all_caps is True

    def test_add_text_defaults_false(self):
        rc = RunCollection()
        run = rc.add_text("hello")
        assert run.small_caps is False
        assert run.all_caps is False


class TestRunFormattingFields:
    def test_small_caps_default_false(self):
        assert RunFormatting().small_caps is False

    def test_all_caps_default_false(self):
        assert RunFormatting().all_caps is False

    def test_explicit_small_caps(self):
        assert RunFormatting(small_caps=True).small_caps is True

    def test_explicit_all_caps(self):
        assert RunFormatting(all_caps=True).all_caps is True


class TestSmallCapsRoundTrip:
    def test_small_caps_survives_to_docx_and_back(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_text("SmallCaps", small_caps=True)

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        run2 = next(r for r in para2.runs if isinstance(r, MutableRun))
        assert run2.small_caps is True

    def test_all_caps_survives_to_docx_and_back(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_text("AllCaps", all_caps=True)

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        run2 = next(r for r in para2.runs if isinstance(r, MutableRun))
        assert run2.all_caps is True
