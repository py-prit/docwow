"""Tests for bookmark rendering in docwow.renderer.paragraph_renderer."""
from __future__ import annotations

import pytest

from docwow.models.paragraph import BookmarkStart, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.renderer.paragraph_renderer import render_paragraph


def _para_with_bookmark(name: str, text: str = "Hello") -> Paragraph:
    return Paragraph(
        runs=(BookmarkStart(name=name), TextRun(text=text)),
        formatting=ParagraphFormatting(),
    )


class TestRenderBookmark:
    def test_bookmark_renders_anchor_tag(self):
        html = render_paragraph(_para_with_bookmark("intro"))
        assert "<a " in html

    def test_bookmark_has_id_attribute(self):
        html = render_paragraph(_para_with_bookmark("intro"))
        assert 'id="intro"' in html

    def test_bookmark_has_dw_bookmark_class(self):
        html = render_paragraph(_para_with_bookmark("intro"))
        assert 'class="dw-bookmark"' in html

    def test_bookmark_has_data_dw_bookmark_attribute(self):
        html = render_paragraph(_para_with_bookmark("intro"))
        assert 'data-dw-bookmark="intro"' in html

    def test_bookmark_anchor_is_empty(self):
        html = render_paragraph(_para_with_bookmark("intro"))
        assert '<a id="intro" class="dw-bookmark" data-dw-bookmark="intro"></a>' in html

    def test_bookmark_name_html_escaped(self):
        html = render_paragraph(_para_with_bookmark('a"b'))
        assert 'id="a&quot;b"' in html
        assert 'data-dw-bookmark="a&quot;b"' in html

    def test_bookmark_and_text_both_rendered(self):
        html = render_paragraph(_para_with_bookmark("sec1", text="Section One"))
        assert 'id="sec1"' in html
        assert "Section One" in html

    def test_bookmark_only_paragraph(self):
        para = Paragraph(
            runs=(BookmarkStart(name="anchor"),),
            formatting=ParagraphFormatting(),
        )
        html = render_paragraph(para)
        assert 'id="anchor"' in html

    def test_multiple_bookmarks_all_rendered(self):
        para = Paragraph(
            runs=(
                BookmarkStart(name="first"),
                TextRun(text="middle"),
                BookmarkStart(name="second"),
            ),
            formatting=ParagraphFormatting(),
        )
        html = render_paragraph(para)
        assert 'id="first"' in html
        assert 'id="second"' in html
