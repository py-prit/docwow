"""Tests for paragraph and table cell shading via the mutable API."""

from __future__ import annotations

import pytest

from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.table import MutableTable, MutableTableCell, MutableTableRow
from docwow.models.styles import ParagraphFormatting
from docwow.models.table import TableCell


# ---------------------------------------------------------------------------
# MutableParagraph shading
# ---------------------------------------------------------------------------

class TestMutableParagraphShading:
    def test_default_shading_is_none(self):
        para = MutableParagraph()
        assert para.shading is None

    def test_set_shading_hex(self):
        para = MutableParagraph()
        result = para.set_shading("4472C4")
        assert para.shading == "4472C4"
        assert result is para  # chainable

    def test_set_shading_normalises_to_uppercase(self):
        para = MutableParagraph()
        para.set_shading("4472c4")
        assert para.shading == "4472C4"

    def test_set_shading_none_clears(self):
        para = MutableParagraph()
        para.set_shading("FF0000")
        para.set_shading(None)
        assert para.shading is None

    def test_shading_preserved_through_other_setters(self):
        para = MutableParagraph()
        para.set_shading("4472C4")
        para.set_alignment("center")
        para.set_indent(left_pt=12.0)
        para.set_spacing(before_pt=6.0)
        para.set_keep_together(True)
        para.set_keep_with_next(True)
        para.set_page_break_before(True)
        para.set_style("Heading1")
        assert para.shading == "4472C4"

    def test_to_frozen_carries_shading(self):
        para = MutableParagraph()
        para.set_shading("4472C4")
        frozen = para._to_frozen()
        assert frozen.formatting.shading == "4472C4"

    def test_to_frozen_no_shading(self):
        para = MutableParagraph()
        frozen = para._to_frozen()
        assert frozen.formatting.shading is None

    def test_init_with_formatting_shading(self):
        fmt = ParagraphFormatting(shading="ABCDEF")
        para = MutableParagraph(formatting=fmt)
        assert para.shading == "ABCDEF"


# ---------------------------------------------------------------------------
# MutableTableCell shading
# ---------------------------------------------------------------------------

class TestMutableTableCellShading:
    def test_default_shading_is_none(self):
        cell = MutableTableCell()
        assert cell.shading is None

    def test_set_shading(self):
        cell = MutableTableCell()
        result = cell.set_shading("ED7D31")
        assert cell.shading == "ED7D31"
        assert result is cell  # chainable

    def test_set_shading_normalises_to_uppercase(self):
        cell = MutableTableCell()
        cell.set_shading("ed7d31")
        assert cell.shading == "ED7D31"

    def test_set_shading_none_clears(self):
        cell = MutableTableCell()
        cell.set_shading("ED7D31")
        cell.set_shading(None)
        assert cell.shading is None

    def test_to_frozen_carries_shading(self):
        cell = MutableTableCell(shading="ED7D31")
        frozen = cell._to_frozen()
        assert frozen.shading == "ED7D31"

    def test_init_with_shading(self):
        cell = MutableTableCell(shading="123456")
        assert cell.shading == "123456"


# ---------------------------------------------------------------------------
# Round-trip: ParagraphFormatting shading field
# ---------------------------------------------------------------------------

class TestParagraphFormattingShadingField:
    def test_default_is_none(self):
        fmt = ParagraphFormatting()
        assert fmt.shading is None

    def test_explicit_value(self):
        fmt = ParagraphFormatting(shading="FF0000")
        assert fmt.shading == "FF0000"


# ---------------------------------------------------------------------------
# Round-trip: TableCell shading field
# ---------------------------------------------------------------------------

class TestTableCellShadingField:
    def test_default_is_none(self):
        cell = TableCell(paragraphs=())
        assert cell.shading is None

    def test_explicit_value(self):
        cell = TableCell(paragraphs=(), shading="ED7D31")
        assert cell.shading == "ED7D31"
