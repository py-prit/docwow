"""Tests for block element parsing (h1-h6, p, div, blockquote, pre, hr)."""
from __future__ import annotations

import warnings
import pytest

import docwow
from docwow.html_parser.generic.html_parser import parse_foreign_html
from docwow.models.paragraph import Paragraph, TextRun
from docwow.warnings import DocwowConversionWarning


def _parse(html: str) -> tuple:
    return parse_foreign_html(html).body


def _paras(html: str) -> list[Paragraph]:
    return [e for e in _parse(html) if isinstance(e, Paragraph)]


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------

class TestHeadings:
    def test_h1_style(self):
        paras = _paras("<h1>Title</h1>")
        assert paras[0].formatting.style_id == "Heading1"

    def test_h2_style(self):
        assert _paras("<h2>Sub</h2>")[0].formatting.style_id == "Heading2"

    def test_h6_style(self):
        assert _paras("<h6>tiny</h6>")[0].formatting.style_id == "Heading6"

    def test_heading_text(self):
        assert _paras("<h1>Hello World</h1>")[0].runs[0].text == "Hello World"

    def test_heading_produces_paragraph(self):
        paras = _paras("<h1>Title</h1>")
        assert len(paras) == 1
        assert isinstance(paras[0], Paragraph)


# ---------------------------------------------------------------------------
# Paragraphs
# ---------------------------------------------------------------------------

class TestParagraphs:
    def test_basic_paragraph(self):
        paras = _paras("<p>Hello</p>")
        assert len(paras) == 1
        assert paras[0].runs[0].text == "Hello"

    def test_multiple_paragraphs(self):
        paras = _paras("<p>First</p><p>Second</p>")
        assert len(paras) == 2
        assert paras[0].runs[0].text == "First"
        assert paras[1].runs[0].text == "Second"

    def test_empty_paragraph_skipped(self):
        paras = _paras("<p></p>")
        assert len(paras) == 0

    def test_whitespace_only_paragraph_skipped(self):
        paras = _paras("<p>   </p>")
        assert len(paras) == 0

    def test_paragraph_no_style_id(self):
        paras = _paras("<p>text</p>")
        assert paras[0].formatting.style_id is None


# ---------------------------------------------------------------------------
# Divs
# ---------------------------------------------------------------------------

class TestDivs:
    def test_div_with_text_becomes_paragraph(self):
        paras = _paras("<div>Hello</div>")
        assert len(paras) == 1
        assert paras[0].runs[0].text == "Hello"

    def test_div_with_block_children_transparent(self):
        paras = _paras("<div><p>First</p><p>Second</p></div>")
        assert len(paras) == 2

    def test_nested_divs_with_text(self):
        paras = _paras("<div><div>inner</div></div>")
        assert len(paras) == 1
        assert paras[0].runs[0].text == "inner"

    def test_mixed_div_discards_loose_text(self):
        # loose text + block child → discard loose text, keep p
        paras = _paras("<div>loose text<p>paragraph</p></div>")
        texts = [p.runs[0].text for p in paras]
        assert "paragraph" in texts


# ---------------------------------------------------------------------------
# Blockquote
# ---------------------------------------------------------------------------

class TestBlockquote:
    def test_blockquote_indents_paragraph(self):
        paras = _paras("<blockquote><p>Quoted</p></blockquote>")
        assert paras[0].formatting.indent_left_pt == 36.0

    def test_nested_blockquote_double_indent(self):
        paras = _paras("<blockquote><blockquote><p>Deep</p></blockquote></blockquote>")
        assert paras[0].formatting.indent_left_pt == 72.0

    def test_blockquote_text_preserved(self):
        paras = _paras("<blockquote><p>Quote text</p></blockquote>")
        assert paras[0].runs[0].text == "Quote text"


# ---------------------------------------------------------------------------
# Pre
# ---------------------------------------------------------------------------

class TestPre:
    def test_pre_uses_courier_new(self):
        paras = _paras("<pre>code here</pre>")
        assert paras[0].runs[0].formatting.font_name == "Courier New"

    def test_pre_preserves_whitespace(self):
        paras = _paras("<pre>line1\nline2\n  indented</pre>")
        text = paras[0].runs[0].text
        assert "line1" in text
        assert "line2" in text


# ---------------------------------------------------------------------------
# HR
# ---------------------------------------------------------------------------

class TestHr:
    def test_hr_produces_paragraph(self):
        body = _parse("<hr>")
        assert len(body) == 1
        assert isinstance(body[0], Paragraph)


# ---------------------------------------------------------------------------
# CSS on paragraphs
# ---------------------------------------------------------------------------

class TestParagraphCss:
    def test_text_align_center(self):
        paras = _paras('<p style="text-align: center">text</p>')
        assert paras[0].formatting.alignment == "center"

    def test_text_align_right(self):
        paras = _paras('<p style="text-align: right">text</p>')
        assert paras[0].formatting.alignment == "right"

    def test_margin_left(self):
        paras = _paras('<p style="margin-left: 36px">text</p>')
        assert paras[0].formatting.indent_left_pt == pytest.approx(27.0)

    def test_padding_left(self):
        paras = _paras('<p style="padding-left: 36pt">text</p>')
        assert paras[0].formatting.indent_left_pt == pytest.approx(36.0)

    def test_margin_top(self):
        paras = _paras('<p style="margin-top: 12pt">text</p>')
        assert paras[0].formatting.space_before_pt == pytest.approx(12.0)

    def test_background_color_hex(self):
        paras = _paras('<p style="background-color: #FF0000">text</p>')
        assert paras[0].formatting.shading == "FF0000"

    def test_background_color_named(self):
        paras = _paras('<p style="background-color: yellow">text</p>')
        assert paras[0].formatting.shading == "FFFF00"

    def test_style_tag_applied(self):
        html = "<html><head><style>p { text-align: center; }</style></head><body><p>text</p></body></html>"
        paras = _paras(html)
        assert paras[0].formatting.alignment == "center"

    def test_class_style_applied(self):
        html = "<html><head><style>.intro { text-align: right; }</style></head><body><p class=\"intro\">text</p></body></html>"
        paras = _paras(html)
        assert paras[0].formatting.alignment == "right"


# ---------------------------------------------------------------------------
# Transparent / structural tags
# ---------------------------------------------------------------------------

class TestTransparentTags:
    def test_section_transparent(self):
        paras = _paras("<section><p>text</p></section>")
        assert len(paras) == 1

    def test_article_transparent(self):
        paras = _paras("<article><p>text</p></article>")
        assert len(paras) == 1

    def test_main_transparent(self):
        paras = _paras("<main><p>text</p></main>")
        assert len(paras) == 1


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_unsupported_tag_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _parse("<canvas>chart</canvas>")
        assert any(issubclass(w.category, DocwowConversionWarning) for w in caught)

    def test_unsupported_tag_includes_github_link(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _parse("<iframe src='x'></iframe>")
        msgs = [str(w.message) for w in caught if issubclass(w.category, DocwowConversionWarning)]
        assert any("github.com" in m for m in msgs)


# ---------------------------------------------------------------------------
# Document model integrity
# ---------------------------------------------------------------------------

class TestDocumentModel:
    def test_heading_style_in_document_styles(self):
        doc = parse_foreign_html("<h1>Title</h1>")
        style_ids = {s.style_id for s in doc.styles}
        assert "Heading1" in style_ids

    def test_produces_valid_docx(self):
        result = docwow.to_docx(
            "<h1>Title</h1><p>Body text.</p><blockquote><p>Quote</p></blockquote>",
            is_foreign_html=True,
        )
        assert result[:2] == b"PK"

    def test_full_html_document(self):
        html = """
        <html>
        <head><style>h1 { text-align: center; }</style></head>
        <body>
            <h1>Title</h1>
            <p>Intro paragraph.</p>
            <section>
                <h2>Section</h2>
                <p>Section content.</p>
            </section>
            <blockquote><p>A quote.</p></blockquote>
            <pre>code block</pre>
            <hr>
        </body>
        </html>
        """
        paras = _paras(html)
        assert len(paras) >= 5
        assert paras[0].formatting.style_id == "Heading1"
        assert paras[0].formatting.alignment == "center"
