"""Tests for MutableListItem."""
from __future__ import annotations

import pytest

from docwow.api.list_item import MutableListItem
from docwow.api.paragraph import MutableParagraph
from docwow.models.paragraph import Paragraph


class TestMutableListItem:
    def test_inherits_mutable_paragraph(self):
        item = MutableListItem()
        assert isinstance(item, MutableParagraph)

    def test_defaults(self):
        item = MutableListItem()
        assert item.level == 0
        assert item.num_id == "1"
        assert item.get_text() == ""

    def test_with_text(self):
        item = MutableListItem("hello")
        assert item.get_text() == "hello"

    def test_with_level_and_num_id(self):
        item = MutableListItem("x", num_id="3", level=2)
        assert item.level == 2
        assert item.num_id == "3"

    def test_set_level(self):
        item = MutableListItem()
        result = item.set_level(3)
        assert item.level == 3
        assert result is item

    def test_set_level_boundary_values(self):
        item = MutableListItem()
        item.set_level(0)
        assert item.level == 0
        item.set_level(8)
        assert item.level == 8

    def test_set_num_id(self):
        item = MutableListItem()
        result = item.set_num_id("5")
        assert item.num_id == "5"
        assert result is item

    def test_inherits_para_methods(self):
        item = MutableListItem("hello")
        item.set_bold(True)
        assert item.runs[0].bold is True

    def test_inherits_set_style(self):
        item = MutableListItem()
        item.set_style("ListParagraph")
        assert item.style_id == "ListParagraph"


class TestMutableListItemLevelValidation:
    def test_level_below_zero(self):
        with pytest.raises(ValueError, match="0 and 8"):
            MutableListItem(level=-1)

    def test_level_above_eight(self):
        with pytest.raises(ValueError, match="0 and 8"):
            MutableListItem(level=9)

    def test_set_level_invalid(self):
        item = MutableListItem()
        with pytest.raises(ValueError, match="0 and 8"):
            item.set_level(9)

    def test_set_level_negative(self):
        item = MutableListItem()
        with pytest.raises(ValueError):
            item.set_level(-1)


class TestMutableListItemToFrozen:
    def test_produces_paragraph(self):
        item = MutableListItem("bullet point", level=1, num_id="2")
        frozen = item._to_frozen()
        assert isinstance(frozen, Paragraph)

    def test_list_info_populated(self):
        item = MutableListItem("x", level=2, num_id="3")
        frozen = item._to_frozen()
        assert frozen.list_info is not None
        assert frozen.list_info.level == 2
        assert frozen.list_info.num_id == "3"

    def test_text_preserved(self):
        item = MutableListItem("my item")
        frozen = item._to_frozen()
        assert frozen.runs[0].text == "my item"

    def test_repr(self):
        item = MutableListItem("hello", level=1)
        r = repr(item)
        assert "MutableListItem" in r
        assert "hello" in r
        assert "level=1" in r
