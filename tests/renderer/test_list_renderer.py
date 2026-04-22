"""Tests for docwow.renderer.list_renderer."""
import pytest
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.renderer.list_renderer import render_list_group, _list_tag


def _para(text, num_id="1", level=0):
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(),
        list_info=ListInfo(num_id=num_id, level=level),
    )


def _numbering(num_id, num_fmt="bullet"):
    lvl = ListLevel(level=0, num_fmt=num_fmt)
    return NumberingDefinition(abstract_num_id=num_id, levels=(lvl,))


BULLET_ND = (_numbering("1", "bullet"),)
DECIMAL_ND = (_numbering("1", "decimal"),)


class TestRenderListGroupEmpty:
    def test_empty_list_returns_empty_string(self):
        assert render_list_group([], BULLET_ND) == ""


class TestRenderListGroupSingleLevel:
    def test_produces_ul_for_bullet(self):
        paras = [_para("Item 1"), _para("Item 2")]
        html = render_list_group(paras, BULLET_ND)
        assert "<ul " in html
        assert "</ul>" in html

    def test_produces_ol_for_decimal(self):
        paras = [_para("Item 1")]
        html = render_list_group(paras, DECIMAL_ND)
        assert "<ol " in html
        assert "</ol>" in html

    def test_dw_list_class(self):
        html = render_list_group([_para("A")], BULLET_ND)
        assert 'class="dw-list"' in html

    def test_data_dw_num_id_on_list(self):
        html = render_list_group([_para("A", num_id="3")], (_numbering("3"),))
        assert 'data-dw-num-id="3"' in html

    def test_li_tag_present(self):
        html = render_list_group([_para("A")], BULLET_ND)
        assert "<li " in html
        assert "</li>" in html

    def test_dw_li_class(self):
        html = render_list_group([_para("A")], BULLET_ND)
        assert 'class="dw-li"' in html

    def test_data_dw_level_on_li(self):
        html = render_list_group([_para("A", level=0)], BULLET_ND)
        assert 'data-dw-level="0"' in html

    def test_item_text_in_output(self):
        html = render_list_group([_para("My item")], BULLET_ND)
        assert "My item" in html

    def test_multiple_items_at_same_level(self):
        paras = [_para(f"Item {i}") for i in range(1, 4)]
        html = render_list_group(paras, BULLET_ND)
        assert html.count("<li ") == 3
        assert "Item 1" in html
        assert "Item 2" in html
        assert "Item 3" in html

    def test_single_ul_for_flat_list(self):
        paras = [_para(f"Item {i}") for i in range(3)]
        html = render_list_group(paras, BULLET_ND)
        assert html.count("<ul ") == 1

    def test_all_lists_closed(self):
        paras = [_para("A"), _para("B")]
        html = render_list_group(paras, BULLET_ND)
        assert html.count("<ul") == html.count("</ul>")
        assert html.count("<li") == html.count("</li>")


class TestRenderListGroupNested:
    def test_nested_level_produces_nested_ul(self):
        paras = [
            _para("Level 0", level=0),
            _para("Level 1", level=1),
        ]
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(
                ListLevel(level=0, num_fmt="bullet"),
                ListLevel(level=1, num_fmt="bullet"),
            ),
        ),)
        html = render_list_group(paras, nd)
        assert html.count("<ul ") == 2

    def test_all_elements_closed_after_nesting(self):
        paras = [
            _para("L0", level=0),
            _para("L1", level=1),
            _para("L0 again", level=0),
        ]
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(
                ListLevel(level=0, num_fmt="bullet"),
                ListLevel(level=1, num_fmt="bullet"),
            ),
        ),)
        html = render_list_group(paras, nd)
        assert html.count("<ul") == html.count("</ul>")
        assert html.count("<li") == html.count("</li>")

    def test_different_num_ids_produce_separate_lists(self):
        nd = (_numbering("1"), _numbering("2"))
        paras = [_para("A", num_id="1"), _para("B", num_id="2")]
        html = render_list_group(paras, nd)
        assert html.count("<ul ") == 2


class TestListTag:
    @pytest.mark.parametrize("fmt,expected_tag", [
        ("bullet",      "ul"),
        ("none",        "ul"),
        ("decimal",     "ol"),
        ("lowerLetter", "ol"),
        ("upperLetter", "ol"),
        ("lowerRoman",  "ol"),
        ("upperRoman",  "ol"),
    ])
    def test_list_tag_by_format(self, fmt, expected_tag):
        nd = _numbering("1", fmt)
        assert _list_tag(nd, 0) == expected_tag

    def test_none_nd_defaults_to_ul(self):
        assert _list_tag(None, 0) == "ul"
