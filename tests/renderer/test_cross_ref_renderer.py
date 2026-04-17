"""Tests for CrossRef rendering."""

from __future__ import annotations

from docwow.models.paragraph import CrossRef, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.renderer.paragraph_renderer import render_paragraph


def _para_with_ref(bookmark: str, display: str = "") -> Paragraph:
    return Paragraph(
        runs=(CrossRef(bookmark_name=bookmark, display_text=display),),
        formatting=ParagraphFormatting(),
    )


class TestCrossRefRenderer:
    def test_renders_as_anchor(self):
        html = render_paragraph(_para_with_ref("MyBookmark", "Section 1"))
        assert '<a ' in html
        assert 'class="dw-xref"' in html

    def test_href_points_to_bookmark(self):
        html = render_paragraph(_para_with_ref("MyBookmark", "text"))
        assert 'href="#MyBookmark"' in html

    def test_data_dw_xref_attribute(self):
        html = render_paragraph(_para_with_ref("MyBookmark", "text"))
        assert 'data-dw-xref="MyBookmark"' in html

    def test_display_text_shown(self):
        html = render_paragraph(_para_with_ref("Ref123", "Chapter 2"))
        assert "Chapter 2" in html

    def test_falls_back_to_bookmark_name_when_no_display(self):
        html = render_paragraph(_para_with_ref("Ref123", ""))
        assert "Ref123" in html

    def test_bookmark_name_escaped_in_href(self):
        html = render_paragraph(_para_with_ref("Ref&Bm", "text"))
        assert "Ref&amp;Bm" in html or "Ref%26Bm" in html or "Ref&Bm" not in html.split("href=")[1].split('"')[1]
