"""Tests for TOC rendering in docwow.renderer.toc_renderer."""
from __future__ import annotations

import pytest

from docwow.models.toc import TableOfContents, TocEntry
from docwow.renderer.toc_renderer import render_toc


def _toc(title: str = "Contents", entries: list[tuple[str, str, int]] | None = None) -> TableOfContents:
    return TableOfContents(
        title=title,
        entries=tuple(TocEntry(text=t, url=u, level=l) for t, u, l in (entries or [])),
    )


class TestRenderToc:
    def test_renders_nav_element(self):
        html = render_toc(_toc())
        assert "<nav" in html
        assert "</nav>" in html

    def test_has_dw_toc_class(self):
        html = render_toc(_toc())
        assert 'class="dw-toc"' in html

    def test_has_data_dw_toc_attribute(self):
        html = render_toc(_toc())
        assert 'data-dw-toc="true"' in html

    def test_data_dw_toc_title_attribute(self):
        html = render_toc(_toc("My Table"))
        assert 'data-dw-toc-title="My Table"' in html

    def test_title_rendered_in_paragraph(self):
        html = render_toc(_toc("Contents"))
        assert '<p class="dw-toc-title">Contents</p>' in html

    def test_empty_title_no_title_paragraph(self):
        # data-dw-toc-title="" is always present for round-trip; only the visible
        # <p class="dw-toc-title"> is omitted when the title is empty.
        html = render_toc(_toc(""))
        assert '<p class="dw-toc-title">' not in html

    def test_entries_list_present(self):
        html = render_toc(_toc(entries=[("Intro", "#_Toc1", 1)]))
        assert '<ul class="dw-toc-list">' in html

    def test_entry_renders_li(self):
        html = render_toc(_toc(entries=[("Intro", "#_Toc1", 1)]))
        assert "<li" in html

    def test_entry_has_level_class(self):
        html = render_toc(_toc(entries=[("A", "#x", 2)]))
        assert "dw-toc-level-2" in html

    def test_entry_has_data_dw_toc_level(self):
        html = render_toc(_toc(entries=[("A", "#x", 3)]))
        assert 'data-dw-toc-level="3"' in html

    def test_entry_link_href(self):
        html = render_toc(_toc(entries=[("A", "#_Toc99", 1)]))
        assert 'href="#_Toc99"' in html

    def test_entry_link_text(self):
        html = render_toc(_toc(entries=[("Introduction", "#_Toc1", 1)]))
        assert "Introduction" in html

    def test_entry_link_class(self):
        html = render_toc(_toc(entries=[("A", "#x", 1)]))
        assert 'class="dw-toc-link"' in html

    def test_entry_without_url_renders_span(self):
        html = render_toc(_toc(entries=[("No link", "", 1)]))
        assert 'class="dw-toc-text"' in html
        assert "<a" not in html.split("dw-toc-list")[1].split("</ul>")[0]

    def test_multiple_entries_all_rendered(self):
        html = render_toc(_toc(entries=[
            ("Chapter 1", "#_Toc1", 1),
            ("Section 1.1", "#_Toc2", 2),
            ("Chapter 2", "#_Toc3", 1),
        ]))
        assert "Chapter 1" in html
        assert "Section 1.1" in html
        assert "Chapter 2" in html

    def test_title_html_escaped(self):
        html = render_toc(_toc('<script>'))
        assert "&lt;script&gt;" in html

    def test_entry_text_html_escaped(self):
        html = render_toc(_toc(entries=[('<b>bold</b>', "#x", 1)]))
        assert "&lt;b&gt;" in html

    def test_no_entries_no_list(self):
        html = render_toc(_toc())
        assert "dw-toc-list" not in html
