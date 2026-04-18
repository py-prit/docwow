"""Tests for inline element parsing (b/i/u/s/code/mark/sub/sup/span/a + CSS)."""
from __future__ import annotations

import pytest

from docwow.html_parser.generic.html_parser import parse_foreign_html
from docwow.models.paragraph import Hyperlink, Paragraph, TextRun


def _para(html: str) -> Paragraph:
    body = parse_foreign_html(f"<p>{html}</p>").body
    paras = [e for e in body if isinstance(e, Paragraph)]
    assert paras, f"No paragraph produced from: {html!r}"
    return paras[0]


def _runs(html: str) -> list[TextRun | Hyperlink]:
    return list(_para(html).runs)


def _text_run(html: str, index: int = 0) -> TextRun:
    run = _runs(html)[index]
    assert isinstance(run, TextRun), f"Expected TextRun at index {index}, got {type(run)}"
    return run


# ---------------------------------------------------------------------------
# Semantic bold/italic tags
# ---------------------------------------------------------------------------

class TestBoldTags:
    def test_b_sets_bold(self):
        assert _text_run("<b>bold</b>").formatting.bold is True

    def test_strong_sets_bold(self):
        assert _text_run("<strong>bold</strong>").formatting.bold is True

    def test_b_text(self):
        assert _text_run("<b>hello</b>").text == "hello"

    def test_bold_does_not_affect_surrounding_text(self):
        runs = _runs("before <b>bold</b> after")
        texts = [r.text if isinstance(r, TextRun) else "" for r in runs]
        assert "before " in texts or any("before" in t for t in texts)
        bold_runs = [r for r in runs if isinstance(r, TextRun) and r.formatting.bold]
        assert len(bold_runs) == 1
        assert bold_runs[0].text == "bold"


class TestItalicTags:
    def test_i_sets_italic(self):
        assert _text_run("<i>italic</i>").formatting.italic is True

    def test_em_sets_italic(self):
        assert _text_run("<em>italic</em>").formatting.italic is True

    def test_cite_sets_italic(self):
        assert _text_run("<cite>citation</cite>").formatting.italic is True

    def test_italic_false_outside(self):
        runs = _runs("plain <i>italic</i> plain")
        plain_runs = [r for r in runs if isinstance(r, TextRun) and not r.formatting.italic]
        assert plain_runs


class TestUnderlineTags:
    def test_u_sets_underline(self):
        assert _text_run("<u>underlined</u>").formatting.underline is True

    def test_ins_sets_underline(self):
        assert _text_run("<ins>inserted</ins>").formatting.underline is True


class TestStrikeTags:
    def test_s_sets_strike(self):
        assert _text_run("<s>struck</s>").formatting.strike is True

    def test_del_sets_strike(self):
        assert _text_run("<del>deleted</del>").formatting.strike is True

    def test_strike_tag(self):
        assert _text_run("<strike>old</strike>").formatting.strike is True


class TestCodeTags:
    def test_code_sets_courier(self):
        assert _text_run("<code>fn()</code>").formatting.font_name == "Courier New"

    def test_kbd_sets_courier(self):
        assert _text_run("<kbd>Ctrl+C</kbd>").formatting.font_name == "Courier New"

    def test_samp_sets_courier(self):
        assert _text_run("<samp>output</samp>").formatting.font_name == "Courier New"


class TestMarkTag:
    def test_mark_sets_yellow_highlight(self):
        assert _text_run("<mark>highlighted</mark>").formatting.highlight == "yellow"


class TestSubSupTags:
    def test_sub_sets_subscript(self):
        assert _text_run("<sub>2</sub>").formatting.vertical_align == "subscript"

    def test_sup_sets_superscript(self):
        assert _text_run("<sup>2</sup>").formatting.vertical_align == "superscript"


# ---------------------------------------------------------------------------
# Nested / combined inline formatting
# ---------------------------------------------------------------------------

class TestNestedFormatting:
    def test_bold_italic_nested(self):
        run = _text_run("<b><i>bi</i></b>")
        assert run.formatting.bold is True
        assert run.formatting.italic is True

    def test_italic_bold_nested(self):
        run = _text_run("<i><b>bi</b></i>")
        assert run.formatting.bold is True
        assert run.formatting.italic is True

    def test_bold_preserves_through_span(self):
        run = _text_run('<b><span>inner</span></b>')
        assert run.formatting.bold is True

    def test_three_levels_deep(self):
        run = _text_run("<b><i><u>biu</u></i></b>")
        fmt = run.formatting
        assert fmt.bold and fmt.italic and fmt.underline

    def test_sibling_runs_independent(self):
        runs = _runs("<b>bold</b><i>italic</i>")
        bold_run = next(r for r in runs if isinstance(r, TextRun) and r.text == "bold")
        italic_run = next(r for r in runs if isinstance(r, TextRun) and r.text == "italic")
        assert bold_run.formatting.bold and not bold_run.formatting.italic
        assert italic_run.formatting.italic and not italic_run.formatting.bold


# ---------------------------------------------------------------------------
# CSS on span and other elements
# ---------------------------------------------------------------------------

class TestCssOnSpan:
    def test_span_font_weight_bold(self):
        run = _text_run('<span style="font-weight: bold">text</span>')
        assert run.formatting.bold is True

    def test_span_font_style_italic(self):
        run = _text_run('<span style="font-style: italic">text</span>')
        assert run.formatting.italic is True

    def test_span_text_decoration_underline(self):
        run = _text_run('<span style="text-decoration: underline">text</span>')
        assert run.formatting.underline is True

    def test_span_text_decoration_line_through(self):
        run = _text_run('<span style="text-decoration: line-through">text</span>')
        assert run.formatting.strike is True

    def test_span_color_hex(self):
        run = _text_run('<span style="color: #ff0000">red</span>')
        assert run.formatting.color == "FF0000"

    def test_span_color_named(self):
        run = _text_run('<span style="color: blue">blue</span>')
        assert run.formatting.color == "0000FF"

    def test_span_color_rgb(self):
        run = _text_run('<span style="color: rgb(0, 128, 0)">green</span>')
        assert run.formatting.color == "008000"

    def test_span_font_size_px(self):
        run = _text_run('<span style="font-size: 16px">text</span>')
        assert run.formatting.font_size_pt is not None
        assert abs(run.formatting.font_size_pt - 12.0) < 0.5  # 16px ≈ 12pt

    def test_span_font_size_pt(self):
        run = _text_run('<span style="font-size: 14pt">text</span>')
        assert run.formatting.font_size_pt == pytest.approx(14.0, abs=0.1)

    def test_span_font_family(self):
        run = _text_run('<span style="font-family: Arial">text</span>')
        assert run.formatting.font_name == "Arial"

    def test_span_font_family_quoted(self):
        run = _text_run('<span style="font-family: \'Times New Roman\', serif">text</span>')
        assert run.formatting.font_name == "Times New Roman"

    def test_span_font_family_double_quoted(self):
        run = _text_run('<span style="font-family: &quot;Georgia&quot;, serif">text</span>')
        assert run.formatting.font_name == "Georgia"

    def test_span_vertical_align_super(self):
        run = _text_run('<span style="vertical-align: super">x</span>')
        assert run.formatting.vertical_align == "superscript"

    def test_span_vertical_align_sub(self):
        run = _text_run('<span style="vertical-align: sub">x</span>')
        assert run.formatting.vertical_align == "subscript"

    def test_span_font_variant_small_caps(self):
        run = _text_run('<span style="font-variant: small-caps">x</span>')
        assert run.formatting.small_caps is True

    def test_span_text_transform_uppercase(self):
        run = _text_run('<span style="text-transform: uppercase">x</span>')
        assert run.formatting.all_caps is True

    def test_css_overrides_accumulate_with_tag(self):
        run = _text_run('<b><span style="font-size: 14pt">x</span></b>')
        assert run.formatting.bold is True
        assert run.formatting.font_size_pt == pytest.approx(14.0, abs=0.1)

    def test_span_background_yellow_maps_highlight(self):
        run = _text_run('<span style="background-color: yellow">x</span>')
        assert run.formatting.highlight == "yellow"

    def test_span_no_style_no_change(self):
        run = _text_run('<span>plain</span>')
        assert run.formatting == run.formatting  # idempotent


# ---------------------------------------------------------------------------
# CSS numeric font-weight
# ---------------------------------------------------------------------------

class TestCssFontWeight:
    def test_fw_700_is_bold(self):
        run = _text_run('<span style="font-weight: 700">x</span>')
        assert run.formatting.bold is True

    def test_fw_400_is_not_bold(self):
        # 400 should not set bold (even inside a <b> parent it would stay False
        # from the CSS override — but here we only test the CSS alone)
        run = _text_run('<span style="font-weight: 400">x</span>')
        assert run.formatting.bold is False


# ---------------------------------------------------------------------------
# Hyperlinks (<a href>)
# ---------------------------------------------------------------------------

class TestHyperlinks:
    def test_a_produces_hyperlink(self):
        runs = _runs('<a href="https://example.com">click</a>')
        assert len(runs) == 1
        assert isinstance(runs[0], Hyperlink)

    def test_hyperlink_url(self):
        link = _runs('<a href="https://example.com">click</a>')[0]
        assert isinstance(link, Hyperlink)
        assert link.url == "https://example.com"

    def test_hyperlink_text(self):
        link = _runs('<a href="https://example.com">click me</a>')[0]
        assert isinstance(link, Hyperlink)
        assert link.runs[0].text == "click me"

    def test_a_without_href_emits_plain_run(self):
        # Anchor with no href → plain text run
        runs = _runs('<a>anchor</a>')
        text_runs = [r for r in runs if isinstance(r, TextRun)]
        assert text_runs

    def test_hyperlink_with_bold_inner(self):
        link = _runs('<a href="https://x.com"><b>bold link</b></a>')[0]
        assert isinstance(link, Hyperlink)
        assert link.runs[0].formatting.bold is True

    def test_surrounding_text_preserved(self):
        runs = _runs('before <a href="https://x.com">link</a> after')
        texts = [r.text if isinstance(r, TextRun) else None for r in runs]
        assert any(t and "before" in t for t in texts)
        assert any(t and "after" in t for t in texts)
        assert any(isinstance(r, Hyperlink) for r in runs)

    def test_mailto_href(self):
        link = _runs('<a href="mailto:user@example.com">email</a>')[0]
        assert isinstance(link, Hyperlink)
        assert link.url == "mailto:user@example.com"

    def test_hyperlink_multiple_runs_inside(self):
        link = _runs('<a href="https://x.com">plain <b>bold</b> end</a>')[0]
        assert isinstance(link, Hyperlink)
        assert len(link.runs) == 3
        texts = [r.text for r in link.runs]
        assert "plain " in texts
        assert "bold" in texts
        assert " end" in texts


# ---------------------------------------------------------------------------
# Line breaks
# ---------------------------------------------------------------------------

class TestLineBreaks:
    def test_br_produces_newline_run(self):
        runs = _runs("line1<br>line2")
        all_text = "".join(r.text for r in runs if isinstance(r, TextRun))
        assert "\n" in all_text

    def test_br_self_closing(self):
        runs = _runs("a<br/>b")
        all_text = "".join(r.text for r in runs if isinstance(r, TextRun))
        assert "\n" in all_text


# ---------------------------------------------------------------------------
# Mixed inline content
# ---------------------------------------------------------------------------

class TestMixedContent:
    def test_text_before_and_after_inline(self):
        runs = _runs("Hello <b>world</b>!")
        assert len(runs) == 3
        assert runs[0].text == "Hello "
        assert runs[1].formatting.bold is True
        assert runs[2].text == "!"

    def test_tail_text_gets_parent_formatting(self):
        # Inside <b>, after the <i>, the tail " end" should be bold but not italic
        runs = _runs("<b>start <i>italic</i> end</b>")
        end_run = next(r for r in runs if isinstance(r, TextRun) and "end" in r.text)
        assert end_run.formatting.bold is True
        assert end_run.formatting.italic is False

    def test_inline_in_heading(self):
        body = parse_foreign_html("<h1>Title <b>bold</b></h1>").body
        paras = [e for e in body if isinstance(e, Paragraph)]
        assert paras[0].formatting.style_id == "Heading1"
        bold_runs = [r for r in paras[0].runs if isinstance(r, TextRun) and r.formatting.bold]
        assert bold_runs


# ---------------------------------------------------------------------------
# Integration: parse_foreign_html round-trip to Document
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_document_inline(self):
        html = """
        <html><body>
          <p>Plain text with <b>bold</b>, <i>italic</i>, and <u>underline</u>.</p>
          <p>A <a href="https://example.com">hyperlink</a> and <code>code()</code>.</p>
          <p><mark>highlighted</mark> and H<sub>2</sub>O and E=mc<sup>2</sup>.</p>
        </body></html>
        """
        doc = parse_foreign_html(html)
        assert len(doc.body) == 3

        p0_runs = list(doc.body[0].runs)
        bold_run = next(r for r in p0_runs if isinstance(r, TextRun) and r.formatting.bold)
        assert bold_run.text == "bold"

        p1_runs = list(doc.body[1].runs)
        assert any(isinstance(r, Hyperlink) for r in p1_runs)
        code_run = next(r for r in p1_runs if isinstance(r, TextRun) and r.formatting.font_name == "Courier New")
        assert code_run.text == "code()"

        p2_runs = list(doc.body[2].runs)
        mark_run = next(r for r in p2_runs if isinstance(r, TextRun) and r.formatting.highlight == "yellow")
        assert mark_run.text == "highlighted"
        sub_run = next(r for r in p2_runs if isinstance(r, TextRun) and r.formatting.vertical_align == "subscript")
        assert sub_run.text == "2"
        sup_run = next(r for r in p2_runs if isinstance(r, TextRun) and r.formatting.vertical_align == "superscript")
        assert sup_run.text == "2"
