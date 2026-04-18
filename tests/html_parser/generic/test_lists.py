"""Tests for generic HTML list parsing (ul/ol/li, nesting)."""
from __future__ import annotations

import pytest

from docwow.html_parser.generic.html_parser import parse_foreign_html
from docwow.models.lists import ListInfo
from docwow.models.paragraph import Paragraph, TextRun


def _parse(html: str):
    return parse_foreign_html(html)


def _paras(html: str) -> list[Paragraph]:
    return [e for e in _parse(html).body if isinstance(e, Paragraph)]


def _list_paras(html: str) -> list[Paragraph]:
    return [p for p in _paras(html) if p.list_info is not None]


# ---------------------------------------------------------------------------
# Bullet lists (<ul>)
# ---------------------------------------------------------------------------

class TestBulletList:
    def test_ul_items_have_list_info(self):
        items = _list_paras("<ul><li>A</li><li>B</li></ul>")
        assert len(items) == 2
        assert all(p.list_info is not None for p in items)

    def test_ul_num_fmt_is_bullet(self):
        doc = _parse("<ul><li>A</li></ul>")
        assert len(doc.numbering) == 1
        assert doc.numbering[0].levels[0].num_fmt == "bullet"

    def test_ul_level_zero(self):
        items = _list_paras("<ul><li>A</li></ul>")
        assert items[0].list_info.level == 0

    def test_ul_all_items_same_num_id(self):
        items = _list_paras("<ul><li>A</li><li>B</li><li>C</li></ul>")
        num_ids = {p.list_info.num_id for p in items}
        assert len(num_ids) == 1

    def test_ul_item_text(self):
        items = _list_paras("<ul><li>Hello</li></ul>")
        assert items[0].runs[0].text == "Hello"

    def test_two_separate_ul_different_num_ids(self):
        doc = _parse("<ul><li>A</li></ul><ul><li>B</li></ul>")
        items = [p for p in doc.body if isinstance(p, Paragraph) and p.list_info]
        assert items[0].list_info.num_id != items[1].list_info.num_id
        assert len(doc.numbering) == 2


# ---------------------------------------------------------------------------
# Numbered lists (<ol>)
# ---------------------------------------------------------------------------

class TestNumberedList:
    def test_ol_items_have_list_info(self):
        items = _list_paras("<ol><li>A</li><li>B</li></ol>")
        assert len(items) == 2

    def test_ol_num_fmt_is_decimal(self):
        doc = _parse("<ol><li>A</li></ol>")
        assert doc.numbering[0].levels[0].num_fmt == "decimal"

    def test_ol_level_zero(self):
        items = _list_paras("<ol><li>A</li></ol>")
        assert items[0].list_info.level == 0

    def test_ol_multiple_items(self):
        items = _list_paras("<ol><li>First</li><li>Second</li><li>Third</li></ol>")
        assert len(items) == 3
        texts = [p.runs[0].text for p in items]
        assert texts == ["First", "Second", "Third"]


# ---------------------------------------------------------------------------
# Nested lists
# ---------------------------------------------------------------------------

class TestNestedLists:
    def test_nested_ul_level_increases(self):
        html = "<ul><li>A<ul><li>B</li></ul></li></ul>"
        items = _list_paras(html)
        assert items[0].list_info.level == 0
        assert items[1].list_info.level == 1

    def test_nested_same_num_id(self):
        html = "<ul><li>A<ul><li>B</li></ul></li></ul>"
        items = _list_paras(html)
        assert items[0].list_info.num_id == items[1].list_info.num_id

    def test_nested_only_one_numbering_def(self):
        html = "<ul><li>A<ul><li>B</li></ul></li></ul>"
        doc = _parse(html)
        assert len(doc.numbering) == 1

    def test_three_levels_deep(self):
        html = "<ul><li>L0<ul><li>L1<ul><li>L2</li></ul></li></ul></li></ul>"
        items = _list_paras(html)
        assert items[0].list_info.level == 0
        assert items[1].list_info.level == 1
        assert items[2].list_info.level == 2

    def test_nested_ol_in_ul(self):
        html = "<ul><li>bullet<ol><li>numbered</li></ol></li></ul>"
        items = _list_paras(html)
        assert items[0].list_info.level == 0
        assert items[1].list_info.level == 1

    def test_mixed_siblings(self):
        html = "<ul><li>A</li><li>B<ul><li>B1</li><li>B2</li></ul></li><li>C</li></ul>"
        items = _list_paras(html)
        levels = [p.list_info.level for p in items]
        assert levels == [0, 0, 1, 1, 0]

    def test_multiple_nested_lists_in_one_item(self):
        html = "<ol><li>X<ul><li>a</li></ul><ul><li>b</li></ul></li></ol>"
        items = _list_paras(html)
        assert items[0].list_info.level == 0
        assert items[1].list_info.level == 1
        assert items[2].list_info.level == 1


# ---------------------------------------------------------------------------
# Numbering definitions in Document
# ---------------------------------------------------------------------------

class TestNumberingDefs:
    def test_single_list_one_def(self):
        doc = _parse("<ul><li>A</li></ul>")
        assert len(doc.numbering) == 1

    def test_two_lists_two_defs(self):
        doc = _parse("<ul><li>A</li></ul><ol><li>B</li></ol>")
        assert len(doc.numbering) == 2

    def test_numbering_has_nine_levels(self):
        doc = _parse("<ul><li>A</li></ul>")
        assert len(doc.numbering[0].levels) == 9

    def test_numbering_level_indices(self):
        doc = _parse("<ul><li>A</li></ul>")
        for i, lvl in enumerate(doc.numbering[0].levels):
            assert lvl.level == i

    def test_para_num_id_matches_numbering_def(self):
        doc = _parse("<ul><li>A</li></ul>")
        para = next(p for p in doc.body if isinstance(p, Paragraph) and p.list_info)
        nd_ids = {nd.abstract_num_id for nd in doc.numbering}
        assert para.list_info.num_id in nd_ids

    def test_indent_increases_per_level(self):
        doc = _parse("<ul><li>A</li></ul>")
        levels = doc.numbering[0].levels
        for i in range(1, len(levels)):
            assert levels[i].indent_pt > levels[i - 1].indent_pt


# ---------------------------------------------------------------------------
# Inline formatting inside list items
# ---------------------------------------------------------------------------

class TestListItemFormatting:
    def test_bold_inside_li(self):
        items = _list_paras("<ul><li><b>bold item</b></li></ul>")
        bold_runs = [r for r in items[0].runs if isinstance(r, TextRun) and r.formatting.bold]
        assert bold_runs

    def test_mixed_inline_in_li(self):
        items = _list_paras("<ul><li>plain <b>bold</b> end</li></ul>")
        assert len(items[0].runs) == 3

    def test_hyperlink_inside_li(self):
        from docwow.models.paragraph import Hyperlink
        items = _list_paras('<ul><li><a href="https://x.com">link</a></li></ul>')
        assert any(isinstance(r, Hyperlink) for r in items[0].runs)


# ---------------------------------------------------------------------------
# Mixed content: lists alongside paragraphs
# ---------------------------------------------------------------------------

class TestMixedContent:
    def test_para_before_list(self):
        paras = _paras("<p>Intro</p><ul><li>A</li></ul>")
        assert paras[0].list_info is None
        assert paras[1].list_info is not None

    def test_para_after_list(self):
        paras = _paras("<ul><li>A</li></ul><p>After</p>")
        assert paras[0].list_info is not None
        assert paras[1].list_info is None

    def test_list_between_paragraphs(self):
        paras = _paras("<p>Before</p><ul><li>item</li></ul><p>After</p>")
        assert paras[0].list_info is None
        assert paras[1].list_info is not None
        assert paras[2].list_info is None

    def test_two_lists_separated_by_paragraph(self):
        doc = _parse("<ul><li>A</li></ul><p>mid</p><ul><li>B</li></ul>")
        assert len(doc.numbering) == 2
        items = [p for p in doc.body if isinstance(p, Paragraph) and p.list_info]
        assert items[0].list_info.num_id != items[1].list_info.num_id


# ---------------------------------------------------------------------------
# Integration: parse_foreign_html produces a writable document
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_docx_roundtrip_with_lists(self):
        import docwow
        html = """
        <html><body>
          <p>Introduction</p>
          <ul>
            <li>Bullet one</li>
            <li>Bullet two
              <ul><li>Nested bullet</li></ul>
            </li>
            <li>Bullet three</li>
          </ul>
          <ol>
            <li>Step one</li>
            <li>Step two</li>
          </ol>
        </body></html>
        """
        docx_bytes = docwow.to_docx(html, is_foreign_html=True)
        assert len(docx_bytes) > 0

        doc2 = docwow.open(docx_bytes)
        from docwow.api.list_item import MutableListItem
        list_items = [p for p in doc2.paragraphs if isinstance(p, MutableListItem)]
        texts = [item.get_text().strip() for item in list_items]
        assert "Bullet one" in texts
        assert "Bullet two" in texts
        assert "Nested bullet" in texts
        assert "Step one" in texts
        assert "Step two" in texts

        nested = next(i for i in list_items if i.get_text() == "Nested bullet")
        assert nested.level == 1
