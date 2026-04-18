"""Tests for hidden text (w:vanish) support."""

from __future__ import annotations

from pathlib import Path

import docwow
from docwow.api.run import MutableRun, RunCollection
from docwow.api.paragraph import MutableParagraph
from docwow.models.styles import RunFormatting

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestMutableRunVanish:
    def test_default_vanish_false(self):
        assert MutableRun("hello").vanish is False

    def test_set_vanish(self):
        run = MutableRun("hello")
        result = run.set_vanish()
        assert run.vanish is True
        assert result is run

    def test_set_vanish_false_clears(self):
        run = MutableRun("hello")
        run.set_vanish()
        run.set_vanish(False)
        assert run.vanish is False

    def test_init_with_vanish(self):
        run = MutableRun("hello", vanish=True)
        assert run.vanish is True

    def test_to_frozen_carries_vanish(self):
        run = MutableRun("hello", vanish=True)
        assert run._to_frozen().formatting.vanish is True

    def test_to_frozen_no_vanish(self):
        assert MutableRun("hello")._to_frozen().formatting.vanish is False


class TestRunCollectionAddText:
    def test_add_text_with_vanish(self):
        rc = RunCollection()
        run = rc.add_text("hidden", vanish=True)
        assert run.vanish is True

    def test_add_text_default_not_vanished(self):
        rc = RunCollection()
        run = rc.add_text("visible")
        assert run.vanish is False


class TestRunFormattingVanish:
    def test_vanish_default_false(self):
        assert RunFormatting().vanish is False

    def test_explicit_vanish(self):
        assert RunFormatting(vanish=True).vanish is True


class TestVanishRoundTrip:
    def test_vanish_survives_docx_round_trip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_text("hidden text", vanish=True)

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        run2 = next(r for r in para2.runs if isinstance(r, MutableRun))
        assert run2.vanish is True

    def test_vanish_survives_html_round_trip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_text("hidden text", vanish=True)

        html = docwow.to_html(doc.to_bytes())
        data = docwow.to_docx(html)
        doc2 = docwow.open(data)
        para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        run2 = next(r for r in para2.runs if isinstance(r, MutableRun))
        assert run2.vanish is True

    def test_non_vanished_run_stays_visible(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_text("visible text")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        run2 = next(r for r in para2.runs if isinstance(r, MutableRun))
        assert run2.vanish is False

    def test_vanish_renders_display_none_in_html(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_text("hidden", vanish=True)

        html = docwow.to_html(doc.to_bytes())
        assert "display:none" in html
        assert 'data-dw-vanish="true"' in html
