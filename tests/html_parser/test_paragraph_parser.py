"""Tests for docwow.html_parser.paragraph_parser and ._utils."""
import base64
import pytest
import lxml.html

from docwow.html_parser._utils import has_class, pt_val
from docwow.html_parser.paragraph_parser import parse_paragraph
from docwow.models.paragraph import Hyperlink, ImageRun, TextRun
from docwow.models.lists import ListInfo

PNG = b"\x89PNG\r\n\x1a\n"


def _el(html_str: str):
    """Parse an HTML fragment and return the root element."""
    return lxml.html.fragment_fromstring(html_str)


def _p(inner="", extra_attrs=""):
    return _el(f'<p class="dw-p" {extra_attrs}>{inner}</p>')


def _span(inner="", extra_attrs=""):
    return _el(f'<span class="dw-r" {extra_attrs}>{inner}</span>')


# ---------------------------------------------------------------------------
# _utils
# ---------------------------------------------------------------------------

class TestHasClass:
    def test_present(self):
        el = _el('<div class="foo bar">')
        assert has_class(el, "foo")
        assert has_class(el, "bar")

    def test_absent(self):
        el = _el('<div class="foo">')
        assert not has_class(el, "bar")

    def test_no_class_attr(self):
        el = _el("<div>")
        assert not has_class(el, "foo")

    def test_partial_match_not_counted(self):
        el = _el('<div class="foobar">')
        assert not has_class(el, "foo")


class TestPtVal:
    def test_integer_pt(self):
        assert pt_val("36pt") == 36.0

    def test_float_pt(self):
        assert pt_val("36.5pt") == 36.5

    def test_none_returns_none(self):
        assert pt_val(None) is None

    def test_none_with_default(self):
        assert pt_val(None, 0.0) == 0.0

    def test_empty_string_returns_default(self):
        assert pt_val("", 99.0) == 99.0

    def test_no_pt_suffix_returns_default(self):
        assert pt_val("36px", 0.0) == 0.0

    def test_strips_whitespace(self):
        assert pt_val("  12pt  ") == 12.0

    def test_non_numeric_pt_returns_default(self):
        assert pt_val("notapt", 0.0) == 0.0

    def test_non_numeric_with_pt_suffix_returns_default(self):
        assert pt_val("xpt", 0.0) == 0.0


# ---------------------------------------------------------------------------
# Paragraph formatting
# ---------------------------------------------------------------------------

class TestParagraphFormatting:
    def test_default_formatting(self):
        para = parse_paragraph(_p())
        fmt = para.formatting
        assert fmt.style_id is None
        assert fmt.alignment is None
        assert fmt.indent_left_pt == 0.0
        assert fmt.indent_right_pt == 0.0
        assert fmt.indent_first_line_pt == 0.0
        assert fmt.space_before_pt == 0.0
        assert fmt.space_after_pt == 0.0
        assert fmt.line_spacing_pt is None
        assert fmt.keep_together is False
        assert fmt.keep_with_next is False
        assert fmt.page_break_before is False

    def test_style_id(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-style="Heading1"'))
        assert para.formatting.style_id == "Heading1"

    def test_alignment(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-alignment="center"'))
        assert para.formatting.alignment == "center"

    def test_indent_left(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-indent-left="36pt"'))
        assert para.formatting.indent_left_pt == 36.0

    def test_indent_right(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-indent-right="18pt"'))
        assert para.formatting.indent_right_pt == 18.0

    def test_indent_first_line(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-indent-first-line="18pt"'))
        assert para.formatting.indent_first_line_pt == 18.0

    def test_space_before(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-space-before="12pt"'))
        assert para.formatting.space_before_pt == 12.0

    def test_space_after(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-space-after="8pt"'))
        assert para.formatting.space_after_pt == 8.0

    def test_line_spacing(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-line-spacing="14pt"'))
        assert para.formatting.line_spacing_pt == 14.0

    def test_keep_together(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-keep-together="true"'))
        assert para.formatting.keep_together is True

    def test_keep_with_next(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-keep-with-next="true"'))
        assert para.formatting.keep_with_next is True

    def test_page_break_before(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-page-break-before="true"'))
        assert para.formatting.page_break_before is True


# ---------------------------------------------------------------------------
# List info
# ---------------------------------------------------------------------------

class TestListInfo:
    def test_no_list_info(self):
        para = parse_paragraph(_p())
        assert para.list_info is None

    def test_list_info_level_zero(self):
        para = parse_paragraph(
            _p(extra_attrs='data-dw-num-id="1" data-dw-level="0"')
        )
        assert para.list_info == ListInfo(num_id="1", level=0)

    def test_list_info_level_two(self):
        para = parse_paragraph(
            _p(extra_attrs='data-dw-num-id="3" data-dw-level="2"')
        )
        assert para.list_info == ListInfo(num_id="3", level=2)

    def test_list_info_default_level_zero(self):
        para = parse_paragraph(_p(extra_attrs='data-dw-num-id="2"'))
        assert para.list_info.level == 0


# ---------------------------------------------------------------------------
# Text runs
# ---------------------------------------------------------------------------

class TestTextRun:
    def test_plain_text(self):
        para = parse_paragraph(
            _p('<span class="dw-r">Hello</span>')
        )
        assert len(para.runs) == 1
        assert isinstance(para.runs[0], TextRun)
        assert para.runs[0].text == "Hello"

    def test_empty_span(self):
        para = parse_paragraph(_p('<span class="dw-r"></span>'))
        assert para.runs[0].text == ""

    def test_newline_from_br(self):
        para = parse_paragraph(_p('<span class="dw-r">line1<br>line2</span>'))
        assert para.runs[0].text == "line1\nline2"

    def test_html_entities_decoded(self):
        # lxml decodes &amp; → & automatically
        para = parse_paragraph(_p('<span class="dw-r">a&amp;b</span>'))
        assert para.runs[0].text == "a&b"

    def test_multiple_runs(self):
        para = parse_paragraph(
            _p('<span class="dw-r">A</span><span class="dw-r">B</span>')
        )
        assert len(para.runs) == 2
        assert para.runs[0].text == "A"
        assert para.runs[1].text == "B"

    def test_non_dw_r_span_ignored(self):
        para = parse_paragraph(
            _p('<span class="other">ignored</span><span class="dw-r">kept</span>')
        )
        assert len(para.runs) == 1
        assert para.runs[0].text == "kept"


# ---------------------------------------------------------------------------
# Run formatting
# ---------------------------------------------------------------------------

class TestRunFormatting:
    def _run_fmt(self, attrs: str):
        p = _p(f'<span class="dw-r" {attrs}>x</span>')
        return parse_paragraph(p).runs[0].formatting

    def test_bold(self):
        assert self._run_fmt('data-dw-bold="true"').bold is True

    def test_no_bold_by_default(self):
        assert self._run_fmt("").bold is False

    def test_italic(self):
        assert self._run_fmt('data-dw-italic="true"').italic is True

    def test_underline(self):
        assert self._run_fmt('data-dw-underline="true"').underline is True

    def test_strike(self):
        assert self._run_fmt('data-dw-strike="true"').strike is True

    def test_font_name(self):
        assert self._run_fmt('data-dw-font-name="Arial"').font_name == "Arial"

    def test_font_size(self):
        assert self._run_fmt('data-dw-font-size="14pt"').font_size_pt == 14.0

    def test_color(self):
        assert self._run_fmt('data-dw-color="FF0000"').color == "FF0000"

    def test_highlight(self):
        assert self._run_fmt('data-dw-highlight="yellow"').highlight == "yellow"

    def test_superscript(self):
        assert self._run_fmt('data-dw-vertical-align="superscript"').vertical_align == "superscript"

    def test_subscript(self):
        assert self._run_fmt('data-dw-vertical-align="subscript"').vertical_align == "subscript"

    def test_default_run_formatting_all_none_or_false(self):
        fmt = self._run_fmt("")
        assert fmt.font_name is None
        assert fmt.font_size_pt is None
        assert fmt.color is None
        assert fmt.highlight is None
        assert fmt.vertical_align is None


# ---------------------------------------------------------------------------
# Image runs
# ---------------------------------------------------------------------------

class TestImageRun:
    def _image_html(self, rid="rId1", width="72pt", height="36pt", alt=""):
        b64 = base64.b64encode(PNG).decode("ascii")
        src = f"data:image/png;base64,{b64}"
        return (
            f'<img class="dw-img" src="{src}" alt="{alt}" '
            f'style="width:{width};height:{height};vertical-align:middle" '
            f'data-dw-rid="{rid}" data-dw-width="{width}" data-dw-height="{height}">'
        )

    def test_image_run_type(self):
        para = parse_paragraph(_p(self._image_html()))
        assert len(para.runs) == 1
        assert isinstance(para.runs[0], ImageRun)

    def test_image_content_type(self):
        para = parse_paragraph(_p(self._image_html()))
        assert para.runs[0].image.content_type == "image/png"

    def test_image_data(self):
        para = parse_paragraph(_p(self._image_html()))
        assert para.runs[0].image.data == PNG

    def test_image_dimensions(self):
        para = parse_paragraph(_p(self._image_html()))
        img = para.runs[0].image
        assert img.width_pt == 72.0
        assert img.height_pt == 36.0

    def test_image_rid(self):
        para = parse_paragraph(_p(self._image_html(rid="rId5")))
        assert para.runs[0].image.relationship_id == "rId5"

    def test_image_alt_text(self):
        para = parse_paragraph(_p(self._image_html(alt="A chart")))
        assert para.runs[0].image.alt_text == "A chart"

    def test_empty_src_gives_empty_bytes(self):
        para = parse_paragraph(
            _p('<img class="dw-img" src="" data-dw-width="72pt" data-dw-height="36pt">')
        )
        img = para.runs[0].image
        assert img.data == b""
        assert img.content_type == ""

    def test_data_uri_no_comma_gives_empty(self):
        # data URI without a comma separator
        para = parse_paragraph(
            _p('<img class="dw-img" src="data:image/png;base64" '
               'data-dw-width="72pt" data-dw-height="36pt">')
        )
        img = para.runs[0].image
        assert img.data == b""

    def test_data_uri_invalid_base64_gives_empty(self):
        para = parse_paragraph(
            _p('<img class="dw-img" src="data:image/png;base64,!!!invalid!!!" '
               'data-dw-width="72pt" data-dw-height="36pt">')
        )
        img = para.runs[0].image
        assert img.content_type == "image/png"
        assert img.data == b""


# ---------------------------------------------------------------------------
# Hyperlink parsing
# ---------------------------------------------------------------------------

def _a(url="https://example.com", inner='<span class="dw-r">Click here</span>'):
    return f'<a href="{url}" class="dw-hyperlink" data-dw-href="{url}">{inner}</a>'


class TestHyperlinkParsing:
    def test_hyperlink_run_type(self):
        para = parse_paragraph(_p(_a()))
        assert len(para.runs) == 1
        assert isinstance(para.runs[0], Hyperlink)

    def test_hyperlink_url(self):
        para = parse_paragraph(_p(_a(url="https://example.com")))
        assert para.runs[0].url == "https://example.com"

    def test_hyperlink_text(self):
        para = parse_paragraph(_p(_a(inner='<span class="dw-r">Click here</span>')))
        assert para.runs[0].runs[0].text == "Click here"

    def test_hyperlink_inner_run_type(self):
        para = parse_paragraph(_p(_a()))
        assert isinstance(para.runs[0].runs[0], TextRun)

    def test_hyperlink_multiple_inner_runs(self):
        inner = '<span class="dw-r">Hello </span><span class="dw-r">world</span>'
        para = parse_paragraph(_p(_a(inner=inner)))
        link = para.runs[0]
        assert len(link.runs) == 2
        assert link.runs[0].text == "Hello "
        assert link.runs[1].text == "world"

    def test_mailto_url(self):
        para = parse_paragraph(_p(_a(url="mailto:test@example.com")))
        assert para.runs[0].url == "mailto:test@example.com"

    def test_anchor_without_data_dw_href_not_parsed_as_hyperlink(self):
        # A plain <a> without data-dw-href is ignored
        para = parse_paragraph(_p('<a href="https://example.com">plain link</a>'))
        assert len(para.runs) == 0

    def test_mixed_spans_and_hyperlink(self):
        html = (
            '<span class="dw-r">Before </span>'
            + _a(inner='<span class="dw-r">link</span>')
            + '<span class="dw-r"> after</span>'
        )
        para = parse_paragraph(_p(html))
        assert len(para.runs) == 3
        assert isinstance(para.runs[0], TextRun)
        assert isinstance(para.runs[1], Hyperlink)
        assert isinstance(para.runs[2], TextRun)
