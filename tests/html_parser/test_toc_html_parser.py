"""Tests for TOC parsing in docwow.html_parser.toc_parser."""
from __future__ import annotations

import lxml.html
import pytest

from docwow.html_parser.toc_parser import parse_toc
from docwow.models.toc import TableOfContents, TocEntry


def _nav(inner: str = "", title: str = "Contents") -> object:
    return lxml.html.fragment_fromstring(
        f'<nav class="dw-toc" data-dw-toc="true" data-dw-toc-title="{title}">'
        f'{inner}'
        f'</nav>'
    )


class TestParseToc:
    def test_returns_table_of_contents(self):
        result = parse_toc(_nav())
        assert isinstance(result, TableOfContents)

    def test_title_from_data_attribute(self):
        result = parse_toc(_nav(title="My TOC"))
        assert result.title == "My TOC"

    def test_empty_entries(self):
        result = parse_toc(_nav())
        assert result.entries == ()

    def test_single_entry(self):
        nav = _nav(
            '<ul class="dw-toc-list">'
            '<li class="dw-toc-entry dw-toc-level-1" data-dw-toc-level="1">'
            '<a class="dw-toc-link" href="#_Toc1">Introduction</a>'
            '</li>'
            '</ul>'
        )
        result = parse_toc(nav)
        assert len(result.entries) == 1

    def test_entry_text(self):
        nav = _nav(
            '<ul class="dw-toc-list">'
            '<li class="dw-toc-entry dw-toc-level-1" data-dw-toc-level="1">'
            '<a class="dw-toc-link" href="#_Toc1">Hello World</a>'
            '</li>'
            '</ul>'
        )
        result = parse_toc(nav)
        assert result.entries[0].text == "Hello World"

    def test_entry_url(self):
        nav = _nav(
            '<ul class="dw-toc-list">'
            '<li class="dw-toc-entry dw-toc-level-1" data-dw-toc-level="1">'
            '<a class="dw-toc-link" href="#_TocABC">x</a>'
            '</li>'
            '</ul>'
        )
        result = parse_toc(nav)
        assert result.entries[0].url == "#_TocABC"

    def test_entry_level(self):
        nav = _nav(
            '<ul class="dw-toc-list">'
            '<li class="dw-toc-entry dw-toc-level-2" data-dw-toc-level="2">'
            '<a class="dw-toc-link" href="#x">x</a>'
            '</li>'
            '</ul>'
        )
        result = parse_toc(nav)
        assert result.entries[0].level == 2

    def test_multiple_entries(self):
        nav = _nav(
            '<ul class="dw-toc-list">'
            '<li class="dw-toc-entry dw-toc-level-1" data-dw-toc-level="1">'
            '<a class="dw-toc-link" href="#_Toc1">Chapter 1</a>'
            '</li>'
            '<li class="dw-toc-entry dw-toc-level-2" data-dw-toc-level="2">'
            '<a class="dw-toc-link" href="#_Toc2">Section 1.1</a>'
            '</li>'
            '</ul>'
        )
        result = parse_toc(nav)
        assert len(result.entries) == 2
        assert result.entries[0].text == "Chapter 1"
        assert result.entries[1].text == "Section 1.1"

    def test_entry_without_url_span(self):
        nav = _nav(
            '<ul class="dw-toc-list">'
            '<li class="dw-toc-entry dw-toc-level-1" data-dw-toc-level="1">'
            '<span class="dw-toc-text">No Link Entry</span>'
            '</li>'
            '</ul>'
        )
        result = parse_toc(nav)
        assert result.entries[0].text == "No Link Entry"
        assert result.entries[0].url == ""
