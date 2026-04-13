"""Tests for docwow.renderer.paragraph_renderer."""
import pytest
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo
from docwow.models.paragraph import Hyperlink, ImageRun, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.renderer.paragraph_renderer import (
    render_paragraph,
    _escape_text,
    _highlight_to_css,
    _run_inline_style,
    _para_inline_style,
)

PNG = b"\x89PNG\r\n\x1a\n"


def _text_run(text="Hello", **fmt_kwargs):
    return TextRun(text=text, formatting=RunFormatting(**fmt_kwargs))


def _image_run():
    img = InlineImage(
        relationship_id="rId1", content_type="image/png",
        data=PNG, width_pt=72.0, height_pt=36.0,
    )
    return ImageRun(image=img)


def _para(runs=None, **fmt_kwargs):
    if runs is None:
        runs = (_text_run(),)
    return Paragraph(runs=tuple(runs), formatting=ParagraphFormatting(**fmt_kwargs))


# ---------------------------------------------------------------------------
# render_paragraph — structure
# ---------------------------------------------------------------------------

class TestRenderParagraphStructure:
    def test_produces_p_tag(self):
        html = render_paragraph(_para())
        assert html.startswith("<p ")
        assert html.endswith("</p>")

    def test_always_has_dw_p_class(self):
        assert 'class="dw-p' in render_paragraph(_para())

    def test_style_id_class_added(self):
        p = Paragraph(
            runs=(_text_run(),),
            formatting=ParagraphFormatting(style_id="Heading1"),
        )
        assert "dw-style-Heading1" in render_paragraph(p)

    def test_no_style_no_extra_class(self):
        p = Paragraph(runs=(_text_run(),), formatting=ParagraphFormatting())
        html = render_paragraph(p)
        assert "dw-style-" not in html

    def test_run_inside_p(self):
        html = render_paragraph(_para(runs=(_text_run("Hi"),)))
        assert "<span" in html
        assert "Hi" in html

    def test_multiple_runs(self):
        runs = (_text_run("Hello "), _text_run("world"))
        html = render_paragraph(_para(runs=runs))
        assert "Hello " in html
        assert "world" in html

    def test_empty_runs(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting())
        html = render_paragraph(p)
        assert "<p " in html
        assert "</p>" in html

    def test_image_run_produces_img_tag(self):
        p = Paragraph(runs=(_image_run(),), formatting=ParagraphFormatting())
        html = render_paragraph(p)
        assert "<img " in html

    def test_text_is_escaped(self):
        p = Paragraph(runs=(_text_run("<b>not bold</b>"),), formatting=ParagraphFormatting())
        html = render_paragraph(p)
        assert "&lt;b&gt;" in html
        assert "<b>" not in html


# ---------------------------------------------------------------------------
# render_paragraph — data-dw-* attributes
# ---------------------------------------------------------------------------

class TestRenderParagraphDataAttrs:
    def test_data_dw_style(self):
        p = Paragraph(
            runs=(), formatting=ParagraphFormatting(style_id="Normal"),
        )
        assert 'data-dw-style="Normal"' in render_paragraph(p)

    def test_data_dw_alignment_center(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(alignment="center"))
        assert 'data-dw-alignment="center"' in render_paragraph(p)

    def test_no_data_dw_alignment_when_none(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting())
        assert "data-dw-alignment" not in render_paragraph(p)

    def test_data_dw_indent_left(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(indent_left_pt=36.0))
        assert 'data-dw-indent-left="36pt"' in render_paragraph(p)

    def test_data_dw_indent_right(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(indent_right_pt=18.0))
        assert 'data-dw-indent-right="18pt"' in render_paragraph(p)

    def test_data_dw_indent_first_line(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(indent_first_line_pt=18.0))
        assert 'data-dw-indent-first-line="18pt"' in render_paragraph(p)

    def test_data_dw_space_before(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(space_before_pt=12.0))
        assert 'data-dw-space-before="12pt"' in render_paragraph(p)

    def test_data_dw_space_after(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(space_after_pt=8.0))
        assert 'data-dw-space-after="8pt"' in render_paragraph(p)

    def test_data_dw_line_spacing(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(line_spacing_pt=14.0))
        assert 'data-dw-line-spacing="14pt"' in render_paragraph(p)

    def test_data_dw_keep_together(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(keep_together=True))
        assert 'data-dw-keep-together="true"' in render_paragraph(p)

    def test_data_dw_keep_with_next(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(keep_with_next=True))
        assert 'data-dw-keep-with-next="true"' in render_paragraph(p)

    def test_data_dw_page_break_before(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting(page_break_before=True))
        assert 'data-dw-page-break-before="true"' in render_paragraph(p)

    def test_list_info_attrs(self):
        li = ListInfo(num_id="2", level=1)
        p = Paragraph(runs=(), formatting=ParagraphFormatting(), list_info=li)
        html = render_paragraph(p)
        assert 'data-dw-num-id="2"' in html
        assert 'data-dw-level="1"' in html

    def test_no_list_attrs_when_no_list_info(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting())
        html = render_paragraph(p)
        assert "data-dw-num-id" not in html
        assert "data-dw-level" not in html


# ---------------------------------------------------------------------------
# Run rendering — data-dw-* attributes
# ---------------------------------------------------------------------------

class TestRunDataAttrs:
    def test_bold(self):
        html = render_paragraph(_para(runs=(_text_run(bold=True),)))
        assert 'data-dw-bold="true"' in html

    def test_no_bold_attr_when_false(self):
        html = render_paragraph(_para(runs=(_text_run(bold=False),)))
        assert "data-dw-bold" not in html

    def test_italic(self):
        html = render_paragraph(_para(runs=(_text_run(italic=True),)))
        assert 'data-dw-italic="true"' in html

    def test_underline(self):
        html = render_paragraph(_para(runs=(_text_run(underline=True),)))
        assert 'data-dw-underline="true"' in html

    def test_strike(self):
        html = render_paragraph(_para(runs=(_text_run(strike=True),)))
        assert 'data-dw-strike="true"' in html

    def test_font_name(self):
        html = render_paragraph(_para(runs=(_text_run(font_name="Arial"),)))
        assert 'data-dw-font-name="Arial"' in html

    def test_font_size(self):
        html = render_paragraph(_para(runs=(_text_run(font_size_pt=14.0),)))
        assert 'data-dw-font-size="14pt"' in html

    def test_color(self):
        html = render_paragraph(_para(runs=(_text_run(color="FF0000"),)))
        assert 'data-dw-color="FF0000"' in html

    def test_highlight(self):
        html = render_paragraph(_para(runs=(_text_run(highlight="yellow"),)))
        assert 'data-dw-highlight="yellow"' in html

    def test_superscript(self):
        html = render_paragraph(_para(runs=(_text_run(vertical_align="superscript"),)))
        assert 'data-dw-vertical-align="superscript"' in html

    def test_subscript(self):
        html = render_paragraph(_para(runs=(_text_run(vertical_align="subscript"),)))
        assert 'data-dw-vertical-align="subscript"' in html


# ---------------------------------------------------------------------------
# Run inline styles
# ---------------------------------------------------------------------------

class TestRunInlineStyle:
    def test_bold_css(self):
        assert "font-weight:bold" in _run_inline_style(RunFormatting(bold=True))

    def test_italic_css(self):
        assert "font-style:italic" in _run_inline_style(RunFormatting(italic=True))

    def test_underline_css(self):
        assert "underline" in _run_inline_style(RunFormatting(underline=True))

    def test_strike_css(self):
        assert "line-through" in _run_inline_style(RunFormatting(strike=True))

    def test_underline_and_strike_combined(self):
        style = _run_inline_style(RunFormatting(underline=True, strike=True))
        assert "underline" in style
        assert "line-through" in style

    def test_font_name_css(self):
        assert "font-family:Arial" in _run_inline_style(RunFormatting(font_name="Arial"))

    def test_font_size_css(self):
        assert "font-size:12pt" in _run_inline_style(RunFormatting(font_size_pt=12.0))

    def test_color_css(self):
        assert "color:#FF0000" in _run_inline_style(RunFormatting(color="FF0000"))

    def test_superscript_css(self):
        style = _run_inline_style(RunFormatting(vertical_align="superscript"))
        assert "vertical-align:super" in style

    def test_subscript_css(self):
        style = _run_inline_style(RunFormatting(vertical_align="subscript"))
        assert "vertical-align:sub" in style

    def test_default_formatting_empty_style(self):
        assert _run_inline_style(RunFormatting()) == ""

    def test_highlight_css(self):
        assert "background-color:" in _run_inline_style(RunFormatting(highlight="yellow"))


# ---------------------------------------------------------------------------
# Paragraph inline styles
# ---------------------------------------------------------------------------

class TestParaInlineStyle:
    def test_alignment_center(self):
        assert "text-align:center" in _para_inline_style(ParagraphFormatting(alignment="center"))

    def test_alignment_justify(self):
        assert "text-align:justify" in _para_inline_style(ParagraphFormatting(alignment="justify"))

    def test_indent_left(self):
        assert "padding-left:36pt" in _para_inline_style(ParagraphFormatting(indent_left_pt=36.0))

    def test_space_before(self):
        assert "margin-top:12pt" in _para_inline_style(ParagraphFormatting(space_before_pt=12.0))

    def test_space_after(self):
        assert "margin-bottom:8pt" in _para_inline_style(ParagraphFormatting(space_after_pt=8.0))

    def test_line_spacing(self):
        assert "line-height:14pt" in _para_inline_style(ParagraphFormatting(line_spacing_pt=14.0))

    def test_indent_right(self):
        assert "padding-right:18pt" in _para_inline_style(ParagraphFormatting(indent_right_pt=18.0))

    def test_first_line_indent_positive(self):
        assert "text-indent:18pt" in _para_inline_style(ParagraphFormatting(indent_first_line_pt=18.0))

    def test_default_formatting_empty_style(self):
        assert _para_inline_style(ParagraphFormatting()) == ""


# ---------------------------------------------------------------------------
# Text escaping
# ---------------------------------------------------------------------------

class TestEscapeText:
    def test_plain_text(self):
        assert _escape_text("hello") == "hello"

    def test_ampersand(self):
        assert _escape_text("a&b") == "a&amp;b"

    def test_less_than(self):
        assert _escape_text("<tag>") == "&lt;tag&gt;"

    def test_newline_becomes_br(self):
        assert _escape_text("line1\nline2") == "line1<br>line2"

    def test_empty_string(self):
        assert _escape_text("") == ""


# ---------------------------------------------------------------------------
# Highlight colour mapping
# ---------------------------------------------------------------------------

class TestHighlightToCss:
    @pytest.mark.parametrize("name,expected", [
        ("yellow",    "#FFFF00"),
        ("red",       "#FF0000"),
        ("green",     "#00FF00"),
        ("blue",      "#0000FF"),
        ("cyan",      "#00FFFF"),
        ("magenta",   "#FF00FF"),
        ("black",     "#000000"),
        ("white",     "#FFFFFF"),
        ("darkRed",   "#800000"),
        ("none",      "transparent"),
    ])
    def test_known_highlight(self, name, expected):
        assert _highlight_to_css(name) == expected

    def test_unknown_highlight_defaults_to_yellow(self):
        assert _highlight_to_css("unknownColor") == "yellow"


# ---------------------------------------------------------------------------
# Hyperlink rendering
# ---------------------------------------------------------------------------

def _hyperlink(url="https://example.com", text="Click here"):
    return Hyperlink(url=url, runs=(TextRun(text=text),))


class TestRenderHyperlink:
    def test_renders_anchor_tag(self):
        para = _para(runs=(_hyperlink(),))
        html = render_paragraph(para)
        assert "<a " in html
        assert "</a>" in html

    def test_href_attribute(self):
        para = _para(runs=(_hyperlink(url="https://example.com"),))
        html = render_paragraph(para)
        assert 'href="https://example.com"' in html

    def test_data_dw_href_attribute(self):
        para = _para(runs=(_hyperlink(url="https://example.com"),))
        html = render_paragraph(para)
        assert 'data-dw-href="https://example.com"' in html

    def test_dw_hyperlink_class(self):
        para = _para(runs=(_hyperlink(),))
        html = render_paragraph(para)
        assert 'class="dw-hyperlink"' in html

    def test_link_text_in_inner_span(self):
        para = _para(runs=(_hyperlink(text="Click here"),))
        html = render_paragraph(para)
        assert "Click here" in html
        assert '<span class="dw-r">' in html

    def test_url_special_chars_escaped(self):
        url = 'https://example.com/search?q=hello&lang=en'
        para = _para(runs=(_hyperlink(url=url),))
        html = render_paragraph(para)
        assert "https://example.com/search?q=hello&amp;lang=en" in html

    def test_mailto_url(self):
        para = _para(runs=(_hyperlink(url="mailto:test@example.com", text="email us"),))
        html = render_paragraph(para)
        assert 'href="mailto:test@example.com"' in html

    def test_mixed_runs_and_hyperlink(self):
        text_run = TextRun(text="See ")
        link = _hyperlink(text="this link")
        para = _para(runs=(text_run, link))
        html = render_paragraph(para)
        assert "See " in html
        assert "this link" in html
        assert "<a " in html

    def test_hyperlink_with_multiple_inner_runs(self):
        link = Hyperlink(
            url="https://example.com",
            runs=(TextRun(text="Hello "), TextRun(text="world")),
        )
        para = _para(runs=(link,))
        html = render_paragraph(para)
        assert "Hello " in html
        assert "world" in html
        assert 'href="https://example.com"' in html
