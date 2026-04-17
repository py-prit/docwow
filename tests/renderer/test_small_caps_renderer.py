"""Tests for small-caps and all-caps rendering."""

from __future__ import annotations

from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.renderer.paragraph_renderer import render_paragraph, _run_inline_style


def _text_run(**fmt_kwargs):
    return TextRun(text="Hello", formatting=RunFormatting(**fmt_kwargs))


def _para(run):
    return Paragraph(runs=(run,), formatting=ParagraphFormatting())


class TestSmallCapsRenderer:
    def test_small_caps_data_attr(self):
        html = render_paragraph(_para(_text_run(small_caps=True)))
        assert 'data-dw-small-caps="true"' in html

    def test_no_small_caps_attr_when_false(self):
        html = render_paragraph(_para(_text_run(small_caps=False)))
        assert "data-dw-small-caps" not in html

    def test_small_caps_css(self):
        assert "font-variant:small-caps" in _run_inline_style(RunFormatting(small_caps=True))

    def test_no_small_caps_css_when_false(self):
        assert "font-variant" not in _run_inline_style(RunFormatting(small_caps=False))


class TestAllCapsRenderer:
    def test_all_caps_data_attr(self):
        html = render_paragraph(_para(_text_run(all_caps=True)))
        assert 'data-dw-all-caps="true"' in html

    def test_no_all_caps_attr_when_false(self):
        html = render_paragraph(_para(_text_run(all_caps=False)))
        assert "data-dw-all-caps" not in html

    def test_all_caps_css(self):
        assert "text-transform:uppercase" in _run_inline_style(RunFormatting(all_caps=True))

    def test_no_all_caps_css_when_false(self):
        assert "text-transform" not in _run_inline_style(RunFormatting(all_caps=False))
