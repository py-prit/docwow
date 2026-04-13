"""Tests for MutableParagraph and ParagraphCollection."""
from __future__ import annotations

import pytest

from docwow.api.image import MutableImage
from docwow.api.list_item import MutableListItem
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.run import MutableImageRun, MutableRun, RunCollection
from docwow.api.table import TableView
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.models.table import Table, TableCell, TableRow


# ---------------------------------------------------------------------------
# MutableParagraph
# ---------------------------------------------------------------------------

class TestMutableParagraphConstruction:
    def test_defaults(self):
        para = MutableParagraph()
        assert len(para.runs) == 0
        assert para.style_id is None
        assert para.alignment is None
        assert para.list_info is None

    def test_with_runs(self):
        rc = RunCollection()
        rc.add_text("hello")
        para = MutableParagraph(runs=rc)
        assert len(para.runs) == 1

    def test_with_formatting(self):
        fmt = ParagraphFormatting(style_id="Heading1", alignment="center")
        para = MutableParagraph(formatting=fmt)
        assert para.style_id == "Heading1"
        assert para.alignment == "center"


class TestParaLevelFormatting:
    def test_set_style(self):
        para = MutableParagraph()
        result = para.set_style("Heading1")
        assert para.style_id == "Heading1"
        assert result is para

    def test_set_style_none(self):
        para = MutableParagraph()
        para.set_style("Heading1")
        para.set_style(None)
        assert para.style_id is None

    def test_set_alignment_valid(self):
        para = MutableParagraph()
        for alignment in ("left", "center", "right", "justify", None):
            para.set_alignment(alignment)
            assert para.alignment == alignment

    def test_set_alignment_invalid(self):
        para = MutableParagraph()
        with pytest.raises(ValueError, match="alignment"):
            para.set_alignment("top")

    def test_set_alignment_returns_self(self):
        para = MutableParagraph()
        assert para.set_alignment("center") is para

    def test_set_indent(self):
        para = MutableParagraph()
        para.set_indent(left_pt=36.0, right_pt=18.0, first_line_pt=12.0)
        frozen = para._to_frozen()
        assert frozen.formatting.indent_left_pt == 36.0
        assert frozen.formatting.indent_right_pt == 18.0
        assert frozen.formatting.indent_first_line_pt == 12.0

    def test_set_spacing(self):
        para = MutableParagraph()
        para.set_spacing(before_pt=6.0, after_pt=6.0, line_pt=14.0)
        frozen = para._to_frozen()
        assert frozen.formatting.space_before_pt == 6.0
        assert frozen.formatting.space_after_pt == 6.0
        assert frozen.formatting.line_spacing_pt == 14.0

    def test_set_keep_together(self):
        para = MutableParagraph()
        para.set_keep_together(True)
        assert para._to_frozen().formatting.keep_together is True

    def test_set_keep_with_next(self):
        para = MutableParagraph()
        para.set_keep_with_next(True)
        assert para._to_frozen().formatting.keep_with_next is True

    def test_set_page_break_before(self):
        para = MutableParagraph()
        para.set_page_break_before(True)
        assert para._to_frozen().formatting.page_break_before is True

    def test_formatting_setters_preserve_other_fields(self):
        para = MutableParagraph()
        para.set_style("Normal")
        para.set_alignment("center")
        # Setting indent should not clear style or alignment
        para.set_indent(left_pt=36.0)
        assert para.style_id == "Normal"
        assert para.alignment == "center"


class TestParaLevelConvenience:
    def test_get_text_empty(self):
        para = MutableParagraph()
        assert para.get_text() == ""

    def test_get_text_concatenates(self):
        para = MutableParagraph()
        para.runs.add_text("Hello")
        para.runs.add_text(" world")
        assert para.get_text() == "Hello world"

    def test_get_text_skips_image_runs(self, inline_image):
        para = MutableParagraph()
        para.runs.add_text("before")
        para.runs.append(MutableImageRun(inline_image))
        para.runs.add_text("after")
        assert para.get_text() == "beforeafter"

    def test_set_text_replaces_all_runs(self):
        para = MutableParagraph()
        para.runs.add_text("old1")
        para.runs.add_text("old2")
        para.set_text("new")
        assert len(para.runs) == 1
        assert para.get_text() == "new"

    def test_set_text_returns_self(self):
        para = MutableParagraph()
        assert para.set_text("hi") is para

    def test_set_bold_all_runs(self):
        para = MutableParagraph()
        para.runs.add_text("a")
        para.runs.add_text("b")
        para.set_bold(True)
        assert all(r.bold for r in para.runs if isinstance(r, MutableRun))

    def test_set_bold_false(self):
        para = MutableParagraph()
        para.runs.add_text("a", bold=True)
        para.set_bold(False)
        assert para.runs[0].bold is False

    def test_set_italic_all_runs(self):
        para = MutableParagraph()
        para.runs.add_text("a")
        para.runs.add_text("b")
        para.set_italic()
        assert all(r.italic for r in para.runs if isinstance(r, MutableRun))

    def test_set_underline_all_runs(self):
        para = MutableParagraph()
        para.runs.add_text("a")
        para.set_underline()
        assert para.runs[0].underline is True

    def test_set_font_name_all_runs(self):
        para = MutableParagraph()
        para.runs.add_text("a")
        para.runs.add_text("b")
        para.set_font_name("Arial")
        assert all(r.font_name == "Arial" for r in para.runs if isinstance(r, MutableRun))

    def test_set_font_size_all_runs(self):
        para = MutableParagraph()
        para.runs.add_text("a")
        para.set_font_size(14.0)
        assert para.runs[0].font_size == 14.0

    def test_set_color_all_runs(self):
        para = MutableParagraph()
        para.runs.add_text("a")
        para.set_color("FF0000")
        assert para.runs[0].color == "FF0000"

    def test_para_level_skips_image_runs(self, inline_image):
        para = MutableParagraph()
        para.runs.add_text("text")
        para.runs.append(MutableImageRun(inline_image))
        # Should not raise even though image runs don't have set_bold
        para.set_bold(True)
        assert para.runs[0].bold is True


class TestMutableParagraphToFrozen:
    def test_basic(self):
        para = MutableParagraph()
        para.runs.add_text("hello")
        frozen = para._to_frozen()
        assert isinstance(frozen, Paragraph)
        assert len(frozen.runs) == 1
        assert isinstance(frozen.runs[0], TextRun)
        assert frozen.runs[0].text == "hello"

    def test_formatting_carried(self):
        para = MutableParagraph()
        para.set_style("Heading1")
        para.set_alignment("center")
        frozen = para._to_frozen()
        assert frozen.formatting.style_id == "Heading1"
        assert frozen.formatting.alignment == "center"

    def test_list_info_none(self):
        para = MutableParagraph()
        frozen = para._to_frozen()
        assert frozen.list_info is None

    def test_repr(self):
        para = MutableParagraph()
        para.runs.add_text("hi")
        para.set_style("Normal")
        r = repr(para)
        assert "MutableParagraph" in r
        assert "Normal" in r


# ---------------------------------------------------------------------------
# ParagraphCollection
# ---------------------------------------------------------------------------

class TestParagraphCollection:
    def test_empty(self):
        pc = ParagraphCollection()
        assert len(pc) == 0

    def test_append_and_len(self):
        pc = ParagraphCollection()
        pc.append(MutableParagraph())
        pc.append(MutableParagraph())
        assert len(pc) == 2

    def test_getitem(self):
        pc = ParagraphCollection()
        para = MutableParagraph()
        pc.append(para)
        assert pc[0] is para

    def test_iter(self):
        pc = ParagraphCollection()
        p1 = MutableParagraph()
        p2 = MutableParagraph()
        pc.append(p1)
        pc.append(p2)
        assert list(pc) == [p1, p2]

    def test_insert(self):
        pc = ParagraphCollection()
        p1 = MutableParagraph()
        p2 = MutableParagraph()
        pc.append(p1)
        pc.insert(0, p2)
        assert pc[0] is p2
        assert pc[1] is p1

    def test_remove(self):
        pc = ParagraphCollection()
        p1 = MutableParagraph()
        p2 = MutableParagraph()
        pc.append(p1)
        pc.append(p2)
        pc.remove(0)
        assert len(pc) == 1
        assert pc[0] is p2

    def test_clear(self):
        pc = ParagraphCollection()
        pc.append(MutableParagraph())
        pc.clear()
        assert len(pc) == 0

    def test_add_paragraph(self):
        pc = ParagraphCollection()
        para = pc.add_paragraph("Hello", style_id="Normal")
        assert isinstance(para, MutableParagraph)
        assert para.get_text() == "Hello"
        assert para.style_id == "Normal"
        assert pc[0] is para

    def test_add_paragraph_empty(self):
        pc = ParagraphCollection()
        para = pc.add_paragraph()
        assert para.get_text() == ""

    def test_add_list_item(self):
        pc = ParagraphCollection()
        item = pc.add_list_item("item text", level=1, num_id="2")
        assert isinstance(item, MutableListItem)
        assert item.get_text() == "item text"
        assert item.level == 1
        assert item.num_id == "2"
        assert pc[0] is item

    def test_add_image(self, png_bytes):
        pc = ParagraphCollection()
        img = pc.add_image(png_bytes, "image/png", 100.0, 80.0, alt_text="test")
        assert isinstance(img, MutableImage)
        assert img.width_pt == 100.0
        assert img.height_pt == 80.0
        assert img.alt_text == "test"
        assert pc[0] is img

    def test_accepts_table_view(self):
        pc = ParagraphCollection()
        table = Table(rows=(), width_pt=None, style_id=None)
        tv = TableView(table)
        pc.append(tv)
        assert pc[0] is tv

    def test_accepts_list_item(self):
        pc = ParagraphCollection()
        item = MutableListItem("item")
        pc.append(item)
        assert pc[0] is item

    def test_accepts_mutable_image(self, png_bytes):
        pc = ParagraphCollection()
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        pc.append(img)
        assert pc[0] is img


class TestMutableParagraphReadBack:
    """Formatting properties set via setters must be readable back."""

    def test_indent_readback(self):
        para = MutableParagraph()
        para.set_indent(left_pt=36.0, right_pt=18.0, first_line_pt=12.0)
        assert para.indent_left_pt == 36.0
        assert para.indent_right_pt == 18.0
        assert para.indent_first_line_pt == 12.0

    def test_spacing_readback(self):
        para = MutableParagraph()
        para.set_spacing(before_pt=6.0, after_pt=3.0, line_pt=14.0)
        assert para.space_before_pt == 6.0
        assert para.space_after_pt == 3.0
        assert para.line_spacing_pt == 14.0

    def test_line_spacing_none_by_default(self):
        para = MutableParagraph()
        assert para.line_spacing_pt is None

    def test_keep_together_readback(self):
        para = MutableParagraph()
        assert para.keep_together is False
        para.set_keep_together(True)
        assert para.keep_together is True
        para.set_keep_together(False)
        assert para.keep_together is False

    def test_keep_with_next_readback(self):
        para = MutableParagraph()
        assert para.keep_with_next is False
        para.set_keep_with_next(True)
        assert para.keep_with_next is True

    def test_page_break_before_readback(self):
        para = MutableParagraph()
        assert para.page_break_before is False
        para.set_page_break_before(True)
        assert para.page_break_before is True

    def test_defaults_are_zero(self):
        para = MutableParagraph()
        assert para.indent_left_pt == 0.0
        assert para.indent_right_pt == 0.0
        assert para.indent_first_line_pt == 0.0
        assert para.space_before_pt == 0.0
        assert para.space_after_pt == 0.0

    def test_readback_consistent_with_frozen(self):
        para = MutableParagraph()
        para.set_indent(left_pt=24.0).set_spacing(before_pt=8.0).set_keep_together(True)
        frozen = para._to_frozen()
        assert para.indent_left_pt == frozen.formatting.indent_left_pt
        assert para.space_before_pt == frozen.formatting.space_before_pt
        assert para.keep_together == frozen.formatting.keep_together


class TestParagraphCollectionAddPageBreak:
    def test_add_page_break_appends(self):
        from docwow.models.paragraph import PageBreak
        pc = ParagraphCollection()
        pc.add_paragraph("before")
        result = pc.add_page_break()
        pc.add_paragraph("after")
        assert len(pc) == 3
        assert isinstance(result, PageBreak)
        assert isinstance(pc[1], PageBreak)

    def test_page_break_in_frozen_body(self):
        from docwow.models.paragraph import PageBreak
        pc = ParagraphCollection()
        pc.add_page_break()
        body = pc._to_frozen_body()
        assert isinstance(body[0], PageBreak)


class TestParagraphCollectionTypeEnforcement:
    def test_rejects_frozen_paragraph(self):
        pc = ParagraphCollection()
        with pytest.raises(TypeError, match="frozen Paragraph"):
            pc.append(Paragraph(runs=()))

    def test_rejects_string(self):
        pc = ParagraphCollection()
        with pytest.raises(TypeError):
            pc.append("text")  # type: ignore[arg-type]

    def test_rejects_on_insert(self):
        pc = ParagraphCollection()
        with pytest.raises(TypeError):
            pc.insert(0, Paragraph(runs=()))


class TestParagraphCollectionToFrozenBody:
    def test_empty(self):
        pc = ParagraphCollection()
        assert pc._to_frozen_body() == ()

    def test_paragraphs_in_order(self):
        pc = ParagraphCollection()
        pc.add_paragraph("first")
        pc.add_paragraph("second")
        body = pc._to_frozen_body()
        assert len(body) == 2
        assert isinstance(body[0], Paragraph)
        assert body[0].runs[0].text == "first"
        assert body[1].runs[0].text == "second"

    def test_table_view_passes_through(self):
        pc = ParagraphCollection()
        table = Table(rows=(), width_pt=None, style_id=None)
        tv = TableView(table)
        pc.append(tv)
        body = pc._to_frozen_body()
        assert body[0] is table

    def test_repr(self):
        pc = ParagraphCollection()
        pc.add_paragraph("x")
        assert "1 item" in repr(pc)
