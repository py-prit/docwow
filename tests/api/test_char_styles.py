"""Tests for character style support via the mutable API."""

from __future__ import annotations

from docwow.api.run import MutableRun, RunCollection
from docwow.models.styles import RunFormatting


class TestMutableRunCharStyle:
    def test_default_char_style_is_none(self):
        run = MutableRun("hello")
        assert run.char_style_id is None

    def test_set_char_style(self):
        run = MutableRun("hello")
        result = run.set_char_style("Strong")
        assert run.char_style_id == "Strong"
        assert result is run  # chainable

    def test_set_char_style_none_clears(self):
        run = MutableRun("hello")
        run.set_char_style("Strong")
        run.set_char_style(None)
        assert run.char_style_id is None

    def test_init_with_char_style_id(self):
        run = MutableRun("hello", char_style_id="Emphasis")
        assert run.char_style_id == "Emphasis"

    def test_to_frozen_carries_char_style(self):
        run = MutableRun("hello")
        run.set_char_style("Strong")
        frozen = run._to_frozen()
        assert frozen.formatting.char_style_id == "Strong"

    def test_to_frozen_no_char_style(self):
        run = MutableRun("hello")
        frozen = run._to_frozen()
        assert frozen.formatting.char_style_id is None


class TestRunCollectionAddText:
    def test_add_text_with_char_style(self):
        rc = RunCollection()
        run = rc.add_text("hello", char_style_id="Strong")
        assert run.char_style_id == "Strong"

    def test_add_text_without_char_style(self):
        rc = RunCollection()
        run = rc.add_text("hello")
        assert run.char_style_id is None


class TestRunFormattingCharStyleField:
    def test_default_is_none(self):
        fmt = RunFormatting()
        assert fmt.char_style_id is None

    def test_explicit_value(self):
        fmt = RunFormatting(char_style_id="Strong")
        assert fmt.char_style_id == "Strong"
