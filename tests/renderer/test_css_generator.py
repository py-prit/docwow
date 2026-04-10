"""Tests for docwow.renderer.css_generator."""
import pytest
from docwow.models.document import Document
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.renderer.css_generator import (
    generate_css,
    _document_rule,
    _style_rule,
    _para_fmt_declarations,
    _run_fmt_declarations,
)


def _doc(styles=(), **page_kwargs):
    defaults = dict(
        body=(), numbering=(),
        page_width_pt=595.28, page_height_pt=841.89,
        margin_top_pt=72.0, margin_bottom_pt=72.0,
        margin_left_pt=72.0, margin_right_pt=72.0,
    )
    defaults.update(page_kwargs)
    return Document(styles=styles, **defaults)


def _style(style_id, para_fmt=None, run_fmt=None, style_type="paragraph"):
    return Style(
        style_id=style_id,
        name=style_id,
        style_type=style_type,
        paragraph_fmt=para_fmt,
        run_fmt=run_fmt,
    )


class TestGenerateCss:
    def test_returns_string(self):
        assert isinstance(generate_css(_doc()), str)

    def test_contains_base_css(self):
        css = generate_css(_doc())
        assert ".dw-document" in css
        assert ".dw-p" in css
        assert ".dw-table" in css

    def test_contains_document_rule(self):
        css = generate_css(_doc(page_width_pt=612.0))
        assert "612pt" in css

    def test_style_class_emitted(self):
        styles = (_style("Normal", para_fmt=ParagraphFormatting(alignment="left")),)
        css = generate_css(_doc(styles=styles))
        assert ".dw-style-Normal" in css

    def test_no_style_classes_for_empty_styles(self):
        css = generate_css(_doc())
        assert ".dw-style-" not in css

    def test_style_with_spaces_uses_dashes(self):
        styles = (_style("Heading 1", run_fmt=RunFormatting(bold=True)),)
        css = generate_css(_doc(styles=styles))
        assert ".dw-style-Heading-1" in css

    def test_style_with_no_fmt_skipped(self):
        styles = (_style("Empty"),)
        css = generate_css(_doc(styles=styles))
        assert ".dw-style-Empty" not in css


class TestDocumentRule:
    def test_contains_max_width(self):
        doc = _doc(page_width_pt=595.28)
        assert "max-width:595.28pt" in _document_rule(doc)

    def test_contains_padding(self):
        doc = _doc(margin_top_pt=72.0, margin_right_pt=90.0,
                   margin_bottom_pt=72.0, margin_left_pt=90.0)
        rule = _document_rule(doc)
        assert "72pt" in rule
        assert "90pt" in rule

    def test_selector_is_dw_document(self):
        assert ".dw-document" in _document_rule(_doc())


class TestStyleRule:
    def test_empty_style_returns_empty_string(self):
        s = _style("Normal")
        assert _style_rule(s) == ""

    def test_para_fmt_style_rule(self):
        s = _style("Center", para_fmt=ParagraphFormatting(alignment="center"))
        rule = _style_rule(s)
        assert ".dw-style-Center" in rule
        assert "text-align:center" in rule

    def test_run_fmt_style_rule(self):
        s = _style("Bold", run_fmt=RunFormatting(bold=True))
        rule = _style_rule(s)
        assert ".dw-style-Bold" in rule
        assert "font-weight:bold" in rule

    def test_style_id_with_spaces_uses_dashes(self):
        s = _style("My Style", run_fmt=RunFormatting(bold=True))
        assert ".dw-style-My-Style" in _style_rule(s)


class TestParaFmtDeclarations:
    def test_alignment_left(self):
        assert "text-align:left" in _para_fmt_declarations(ParagraphFormatting(alignment="left"))

    def test_alignment_center(self):
        assert "text-align:center" in _para_fmt_declarations(ParagraphFormatting(alignment="center"))

    def test_alignment_right(self):
        assert "text-align:right" in _para_fmt_declarations(ParagraphFormatting(alignment="right"))

    def test_alignment_justify(self):
        assert "text-align:justify" in _para_fmt_declarations(ParagraphFormatting(alignment="justify"))

    def test_indent_left(self):
        assert "padding-left:36pt" in _para_fmt_declarations(ParagraphFormatting(indent_left_pt=36.0))

    def test_indent_right(self):
        assert "padding-right:18pt" in _para_fmt_declarations(ParagraphFormatting(indent_right_pt=18.0))

    def test_first_line_indent(self):
        assert "text-indent:18pt" in _para_fmt_declarations(ParagraphFormatting(indent_first_line_pt=18.0))

    def test_space_before(self):
        assert "margin-top:12pt" in _para_fmt_declarations(ParagraphFormatting(space_before_pt=12.0))

    def test_space_after(self):
        assert "margin-bottom:8pt" in _para_fmt_declarations(ParagraphFormatting(space_after_pt=8.0))

    def test_line_spacing(self):
        assert "line-height:14pt" in _para_fmt_declarations(ParagraphFormatting(line_spacing_pt=14.0))

    def test_default_formatting_returns_empty(self):
        assert _para_fmt_declarations(ParagraphFormatting()) == []

    def test_zero_indent_not_emitted(self):
        decls = _para_fmt_declarations(ParagraphFormatting(indent_left_pt=0.0))
        assert not any("padding-left" in d for d in decls)


class TestRunFmtDeclarations:
    def test_bold(self):
        assert "font-weight:bold" in _run_fmt_declarations(RunFormatting(bold=True))

    def test_italic(self):
        assert "font-style:italic" in _run_fmt_declarations(RunFormatting(italic=True))

    def test_underline(self):
        decls = _run_fmt_declarations(RunFormatting(underline=True))
        assert any("underline" in d for d in decls)

    def test_strike(self):
        decls = _run_fmt_declarations(RunFormatting(strike=True))
        assert any("line-through" in d for d in decls)

    def test_underline_and_strike_combined(self):
        decls = _run_fmt_declarations(RunFormatting(underline=True, strike=True))
        combined = " ".join(decls)
        assert "underline" in combined
        assert "line-through" in combined

    def test_font_name(self):
        assert "font-family:Arial" in _run_fmt_declarations(RunFormatting(font_name="Arial"))

    def test_font_size(self):
        assert "font-size:12pt" in _run_fmt_declarations(RunFormatting(font_size_pt=12.0))

    def test_color(self):
        assert "color:#FF0000" in _run_fmt_declarations(RunFormatting(color="FF0000"))

    def test_default_formatting_empty(self):
        assert _run_fmt_declarations(RunFormatting()) == []
