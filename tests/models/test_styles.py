"""Tests for docwow.models.styles — RunFormatting, ParagraphFormatting, Style."""

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.styles import ParagraphFormatting, RunFormatting, Style


# ---------------------------------------------------------------------------
# RunFormatting
# ---------------------------------------------------------------------------

class TestRunFormattingDefaults:
    def test_bold_false(self):
        assert RunFormatting().bold is False

    def test_italic_false(self):
        assert RunFormatting().italic is False

    def test_underline_false(self):
        assert RunFormatting().underline is False

    def test_strike_false(self):
        assert RunFormatting().strike is False

    def test_font_name_none(self):
        assert RunFormatting().font_name is None

    def test_font_size_pt_none(self):
        assert RunFormatting().font_size_pt is None

    def test_color_none(self):
        assert RunFormatting().color is None

    def test_highlight_none(self):
        assert RunFormatting().highlight is None

    def test_vertical_align_none(self):
        assert RunFormatting().vertical_align is None


class TestRunFormattingCustomValues:
    def test_bold(self):
        assert RunFormatting(bold=True).bold is True

    def test_italic(self):
        assert RunFormatting(italic=True).italic is True

    def test_underline(self):
        assert RunFormatting(underline=True).underline is True

    def test_strike(self):
        assert RunFormatting(strike=True).strike is True

    def test_font_name(self):
        assert RunFormatting(font_name="Arial").font_name == "Arial"

    def test_font_size_pt(self):
        assert RunFormatting(font_size_pt=12.0).font_size_pt == 12.0

    def test_font_size_pt_fractional(self):
        # Word supports half-point sizes, so fractional pt values are valid
        assert RunFormatting(font_size_pt=10.5).font_size_pt == 10.5

    def test_color_hex(self):
        assert RunFormatting(color="FF0000").color == "FF0000"

    def test_highlight(self):
        assert RunFormatting(highlight="yellow").highlight == "yellow"

    def test_vertical_align_superscript(self):
        assert RunFormatting(vertical_align="superscript").vertical_align == "superscript"

    def test_vertical_align_subscript(self):
        assert RunFormatting(vertical_align="subscript").vertical_align == "subscript"

    def test_all_fields(self):
        fmt = RunFormatting(
            bold=True,
            italic=True,
            underline=True,
            strike=True,
            font_name="Calibri",
            font_size_pt=11.0,
            color="1F2D3E",
            highlight="cyan",
            vertical_align="superscript",
        )
        assert fmt.bold is True
        assert fmt.italic is True
        assert fmt.underline is True
        assert fmt.strike is True
        assert fmt.font_name == "Calibri"
        assert fmt.font_size_pt == 11.0
        assert fmt.color == "1F2D3E"
        assert fmt.highlight == "cyan"
        assert fmt.vertical_align == "superscript"


class TestRunFormattingImmutability:
    def test_cannot_set_bold(self):
        fmt = RunFormatting()
        with pytest.raises(FrozenInstanceError):
            fmt.bold = True  # type: ignore[misc]

    def test_cannot_set_font_size(self):
        fmt = RunFormatting(font_size_pt=12.0)
        with pytest.raises(FrozenInstanceError):
            fmt.font_size_pt = 14.0  # type: ignore[misc]


class TestRunFormattingEquality:
    def test_equal_defaults(self):
        assert RunFormatting() == RunFormatting()

    def test_equal_custom(self):
        assert RunFormatting(bold=True, color="FF0000") == RunFormatting(bold=True, color="FF0000")

    def test_not_equal(self):
        assert RunFormatting(bold=True) != RunFormatting(italic=True)


class TestRunFormattingHashable:
    def test_can_be_used_in_set(self):
        fmt = RunFormatting(bold=True)
        s = {fmt, RunFormatting(), fmt}
        assert len(s) == 2

    def test_can_be_dict_key(self):
        fmt = RunFormatting(color="AABBCC")
        d = {fmt: "value"}
        assert d[fmt] == "value"


# ---------------------------------------------------------------------------
# ParagraphFormatting
# ---------------------------------------------------------------------------

class TestParagraphFormattingDefaults:
    def test_style_id_none(self):
        assert ParagraphFormatting().style_id is None

    def test_alignment_none(self):
        assert ParagraphFormatting().alignment is None

    def test_indent_left_zero(self):
        assert ParagraphFormatting().indent_left_pt == 0.0

    def test_indent_right_zero(self):
        assert ParagraphFormatting().indent_right_pt == 0.0

    def test_indent_first_line_zero(self):
        assert ParagraphFormatting().indent_first_line_pt == 0.0

    def test_space_before_zero(self):
        assert ParagraphFormatting().space_before_pt == 0.0

    def test_space_after_zero(self):
        assert ParagraphFormatting().space_after_pt == 0.0

    def test_line_spacing_none(self):
        assert ParagraphFormatting().line_spacing_pt is None

    def test_keep_together_false(self):
        assert ParagraphFormatting().keep_together is False

    def test_keep_with_next_false(self):
        assert ParagraphFormatting().keep_with_next is False

    def test_page_break_before_false(self):
        assert ParagraphFormatting().page_break_before is False


class TestParagraphFormattingCustomValues:
    def test_style_id(self):
        assert ParagraphFormatting(style_id="Heading1").style_id == "Heading1"

    @pytest.mark.parametrize("alignment", ["left", "center", "right", "justify"])
    def test_alignment_values(self, alignment):
        assert ParagraphFormatting(alignment=alignment).alignment == alignment

    def test_indent_left(self):
        assert ParagraphFormatting(indent_left_pt=36.0).indent_left_pt == 36.0

    def test_indent_right(self):
        assert ParagraphFormatting(indent_right_pt=18.0).indent_right_pt == 18.0

    def test_indent_first_line_positive(self):
        # positive = first-line indent
        assert ParagraphFormatting(indent_first_line_pt=18.0).indent_first_line_pt == 18.0

    def test_indent_first_line_negative(self):
        # negative = hanging indent
        assert ParagraphFormatting(indent_first_line_pt=-18.0).indent_first_line_pt == -18.0

    def test_space_before(self):
        assert ParagraphFormatting(space_before_pt=12.0).space_before_pt == 12.0

    def test_space_after(self):
        assert ParagraphFormatting(space_after_pt=6.0).space_after_pt == 6.0

    def test_line_spacing(self):
        assert ParagraphFormatting(line_spacing_pt=14.0).line_spacing_pt == 14.0

    def test_keep_together(self):
        assert ParagraphFormatting(keep_together=True).keep_together is True

    def test_keep_with_next(self):
        assert ParagraphFormatting(keep_with_next=True).keep_with_next is True

    def test_page_break_before(self):
        assert ParagraphFormatting(page_break_before=True).page_break_before is True


class TestParagraphFormattingImmutability:
    def test_cannot_set_alignment(self):
        fmt = ParagraphFormatting(alignment="left")
        with pytest.raises(FrozenInstanceError):
            fmt.alignment = "center"  # type: ignore[misc]

    def test_cannot_set_style_id(self):
        fmt = ParagraphFormatting()
        with pytest.raises(FrozenInstanceError):
            fmt.style_id = "Heading1"  # type: ignore[misc]


class TestParagraphFormattingEquality:
    def test_equal_defaults(self):
        assert ParagraphFormatting() == ParagraphFormatting()

    def test_not_equal(self):
        assert ParagraphFormatting(alignment="left") != ParagraphFormatting(alignment="right")


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

class TestStyleRequiredFields:
    def test_basic_construction(self):
        s = Style(style_id="Normal", name="Normal", style_type="paragraph")
        assert s.style_id == "Normal"
        assert s.name == "Normal"
        assert s.style_type == "paragraph"

    def test_missing_style_id_raises(self):
        with pytest.raises(TypeError):
            Style(name="Normal", style_type="paragraph")  # type: ignore[call-arg]

    def test_missing_name_raises(self):
        with pytest.raises(TypeError):
            Style(style_id="Normal", style_type="paragraph")  # type: ignore[call-arg]

    def test_missing_style_type_raises(self):
        with pytest.raises(TypeError):
            Style(style_id="Normal", name="Normal")  # type: ignore[call-arg]


class TestStyleOptionalFieldDefaults:
    def test_based_on_none(self):
        s = Style(style_id="Normal", name="Normal", style_type="paragraph")
        assert s.based_on is None

    def test_paragraph_fmt_none(self):
        s = Style(style_id="Normal", name="Normal", style_type="paragraph")
        assert s.paragraph_fmt is None

    def test_run_fmt_none(self):
        s = Style(style_id="Normal", name="Normal", style_type="paragraph")
        assert s.run_fmt is None


class TestStyleWithAllFields:
    def test_full_style(self):
        para_fmt = ParagraphFormatting(alignment="left", space_after_pt=8.0)
        run_fmt = RunFormatting(font_name="Calibri", font_size_pt=11.0)
        s = Style(
            style_id="Normal",
            name="Normal",
            style_type="paragraph",
            based_on="DefaultParagraphFont",
            paragraph_fmt=para_fmt,
            run_fmt=run_fmt,
        )
        assert s.based_on == "DefaultParagraphFont"
        assert s.paragraph_fmt == para_fmt
        assert s.run_fmt == run_fmt


@pytest.mark.parametrize("style_type", ["paragraph", "character", "table", "numbering"])
class TestStyleTypes:
    def test_style_type_stored(self, style_type):
        s = Style(style_id="x", name="x", style_type=style_type)
        assert s.style_type == style_type


class TestStyleImmutability:
    def test_cannot_set_style_id(self):
        s = Style(style_id="Normal", name="Normal", style_type="paragraph")
        with pytest.raises(FrozenInstanceError):
            s.style_id = "Heading1"  # type: ignore[misc]

    def test_cannot_set_based_on(self):
        s = Style(style_id="Heading1", name="heading 1", style_type="paragraph")
        with pytest.raises(FrozenInstanceError):
            s.based_on = "Normal"  # type: ignore[misc]


class TestStyleEquality:
    def test_equal(self):
        s1 = Style(style_id="Normal", name="Normal", style_type="paragraph")
        s2 = Style(style_id="Normal", name="Normal", style_type="paragraph")
        assert s1 == s2

    def test_not_equal_different_id(self):
        s1 = Style(style_id="Normal", name="Normal", style_type="paragraph")
        s2 = Style(style_id="Heading1", name="Normal", style_type="paragraph")
        assert s1 != s2
