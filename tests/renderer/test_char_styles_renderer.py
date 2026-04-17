"""Tests for character style rendering."""

from __future__ import annotations

from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.renderer.paragraph_renderer import render_paragraph


class TestCharStyleRenderer:
    def _para(self, char_style_id: str | None) -> str:
        run = TextRun(text="hello", formatting=RunFormatting(char_style_id=char_style_id))
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        return render_paragraph(para)

    def test_char_style_emits_data_attr(self):
        html = self._para("Strong")
        assert 'data-dw-char-style="Strong"' in html

    def test_char_style_emits_css_class(self):
        html = self._para("Strong")
        assert "dw-cstyle-Strong" in html

    def test_no_char_style_omits_data_attr(self):
        html = self._para(None)
        assert "data-dw-char-style" not in html

    def test_no_char_style_omits_css_class(self):
        html = self._para(None)
        assert "dw-cstyle-" not in html

    def test_char_style_with_spaces_becomes_dashes_in_class(self):
        html = self._para("Intense Quote")
        assert "dw-cstyle-Intense-Quote" in html

    def test_char_style_data_attr_preserved_with_spaces(self):
        html = self._para("Intense Quote")
        assert 'data-dw-char-style="Intense Quote"' in html
