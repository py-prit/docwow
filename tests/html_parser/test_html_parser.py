"""Tests for docwow.html_parser.html_parser — parse_html()."""
import base64
import pytest

from docwow.html_parser.html_parser import parse_html
from docwow.models.document import Document
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.models.table import Table, TableCell, TableRow
from docwow.renderer.html_renderer import render_document

PNG = b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# Helpers — build small Document objects and round-trip them through
# render_document() → parse_html() to verify the parser.
# ---------------------------------------------------------------------------

def _doc(body=(), styles=(), numbering=(), **kw):
    defaults = dict(
        page_width_pt=595.28, page_height_pt=841.89,
        margin_top_pt=72.0, margin_bottom_pt=72.0,
        margin_left_pt=72.0, margin_right_pt=72.0,
    )
    defaults.update(kw)
    return Document(body=body, styles=styles, numbering=numbering, **defaults)


def _para(text="Hello", style_id=None, **fmt_kw):
    fmt = ParagraphFormatting(style_id=style_id, **fmt_kw)
    return Paragraph(runs=(TextRun(text=text),), formatting=fmt)


def _list_para(text, num_id="1", level=0):
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(),
        list_info=ListInfo(num_id=num_id, level=level),
    )


def _numbering(num_id="1", num_fmt="bullet"):
    return NumberingDefinition(
        abstract_num_id=num_id,
        levels=(ListLevel(level=0, num_fmt=num_fmt),),
    )


def _roundtrip(doc: Document) -> Document:
    return parse_html(render_document(doc))


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestParseHtmlErrors:
    def test_missing_dw_document_raises(self):
        with pytest.raises(ValueError, match="dw-document"):
            parse_html("<html><body><p>no wrapper</p></body></html>")

    def test_accepts_bytes(self):
        doc = _doc()
        html = render_document(doc).encode("utf-8")
        parsed = parse_html(html)
        assert isinstance(parsed, Document)

    def test_accepts_str(self):
        parsed = parse_html(render_document(_doc()))
        assert isinstance(parsed, Document)


# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------

class TestPageGeometry:
    def test_a4_defaults(self):
        parsed = _roundtrip(_doc())
        assert parsed.page_width_pt == 595.28
        assert parsed.page_height_pt == 841.89

    def test_letter_size(self):
        parsed = _roundtrip(_doc(page_width_pt=612.0, page_height_pt=792.0))
        assert parsed.page_width_pt == 612.0
        assert parsed.page_height_pt == 792.0

    def test_margins(self):
        parsed = _roundtrip(_doc(
            margin_top_pt=90.0, margin_bottom_pt=90.0,
            margin_left_pt=108.0, margin_right_pt=108.0,
        ))
        assert parsed.margin_top_pt == 90.0
        assert parsed.margin_bottom_pt == 90.0
        assert parsed.margin_left_pt == 108.0
        assert parsed.margin_right_pt == 108.0

    def test_geometry_fallback_when_attrs_absent(self):
        # Minimal HTML with a dw-document div but no geometry attrs
        html = '<html><body><div class="dw-document"></div></body></html>'
        parsed = parse_html(html)
        assert parsed.page_width_pt == 595.28
        assert parsed.margin_top_pt == 72.0


# ---------------------------------------------------------------------------
# Body — paragraphs
# ---------------------------------------------------------------------------

class TestBodyParagraphs:
    def test_empty_body(self):
        assert _roundtrip(_doc()).body == ()

    def test_single_paragraph(self):
        parsed = _roundtrip(_doc(body=(_para("Hello"),)))
        assert len(parsed.body) == 1
        assert isinstance(parsed.body[0], Paragraph)

    def test_paragraph_text(self):
        parsed = _roundtrip(_doc(body=(_para("World"),)))
        assert parsed.body[0].runs[0].text == "World"

    def test_multiple_paragraphs(self):
        doc = _doc(body=(_para("First"), _para("Second")))
        parsed = _roundtrip(doc)
        assert len(parsed.body) == 2
        assert parsed.body[0].runs[0].text == "First"
        assert parsed.body[1].runs[0].text == "Second"

    def test_paragraph_alignment(self):
        para = _para(alignment="center")
        parsed = _roundtrip(_doc(body=(para,)))
        assert parsed.body[0].formatting.alignment == "center"

    def test_paragraph_indent_left(self):
        para = _para(indent_left_pt=36.0)
        parsed = _roundtrip(_doc(body=(para,)))
        assert parsed.body[0].formatting.indent_left_pt == 36.0

    def test_paragraph_space_before(self):
        para = _para(space_before_pt=12.0)
        parsed = _roundtrip(_doc(body=(para,)))
        assert parsed.body[0].formatting.space_before_pt == 12.0

    def test_paragraph_keep_together(self):
        para = _para(keep_together=True)
        parsed = _roundtrip(_doc(body=(para,)))
        assert parsed.body[0].formatting.keep_together is True


# ---------------------------------------------------------------------------
# Body — run formatting round-trip
# ---------------------------------------------------------------------------

class TestRunFormattingRoundTrip:
    def _run_fmt(self, **kw):
        from docwow.models.paragraph import TextRun
        run = TextRun(text="x", formatting=RunFormatting(**kw))
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        parsed = _roundtrip(_doc(body=(para,)))
        return parsed.body[0].runs[0].formatting

    def test_bold(self):
        assert self._run_fmt(bold=True).bold is True

    def test_italic(self):
        assert self._run_fmt(italic=True).italic is True

    def test_underline(self):
        assert self._run_fmt(underline=True).underline is True

    def test_strike(self):
        assert self._run_fmt(strike=True).strike is True

    def test_font_name(self):
        assert self._run_fmt(font_name="Arial").font_name == "Arial"

    def test_font_size(self):
        assert self._run_fmt(font_size_pt=14.0).font_size_pt == 14.0

    def test_color(self):
        assert self._run_fmt(color="FF0000").color == "FF0000"

    def test_highlight(self):
        assert self._run_fmt(highlight="yellow").highlight == "yellow"

    def test_superscript(self):
        assert self._run_fmt(vertical_align="superscript").vertical_align == "superscript"


# ---------------------------------------------------------------------------
# Body — tables
# ---------------------------------------------------------------------------

class TestBodyTables:
    def _simple_table(self, text="cell"):
        p = _para(text)
        cell = TableCell(paragraphs=(p,))
        row = TableRow(cells=(cell,))
        return Table(rows=(row,))

    def test_table_in_body(self):
        parsed = _roundtrip(_doc(body=(self._simple_table(),)))
        assert len(parsed.body) == 1
        assert isinstance(parsed.body[0], Table)

    def test_table_cell_text(self):
        parsed = _roundtrip(_doc(body=(self._simple_table("hello"),)))
        cell_text = parsed.body[0].rows[0].cells[0].paragraphs[0].runs[0].text
        assert cell_text == "hello"

    def test_mixed_body_order(self):
        doc = _doc(body=(_para("before"), self._simple_table(), _para("after")))
        parsed = _roundtrip(doc)
        assert isinstance(parsed.body[0], Paragraph)
        assert isinstance(parsed.body[1], Table)
        assert isinstance(parsed.body[2], Paragraph)

    def test_table_style_id(self):
        t = Table(rows=(), style_id="TableGrid", width_pt=None, col_widths_pt=())
        parsed = _roundtrip(_doc(body=(t,)))
        assert parsed.body[0].style_id == "TableGrid"

    def test_table_col_widths(self):
        t = Table(rows=(), col_widths_pt=(100.0, 150.0, 200.0), width_pt=None)
        parsed = _roundtrip(_doc(body=(t,)))
        assert parsed.body[0].col_widths_pt == (100.0, 150.0, 200.0)


# ---------------------------------------------------------------------------
# Body — lists
# ---------------------------------------------------------------------------

class TestBodyLists:
    def test_list_paragraph_in_body(self):
        nd = (_numbering("1", "bullet"),)
        doc = _doc(body=(_list_para("Item"),), numbering=nd)
        parsed = _roundtrip(doc)
        assert len(parsed.body) == 1
        assert parsed.body[0].list_info is not None

    def test_list_num_id_preserved(self):
        nd = (_numbering("1", "bullet"),)
        doc = _doc(body=(_list_para("Item", num_id="1"),), numbering=nd)
        parsed = _roundtrip(doc)
        assert parsed.body[0].list_info.num_id == "1"

    def test_list_level_preserved(self):
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(
                ListLevel(level=0, num_fmt="bullet"),
                ListLevel(level=1, num_fmt="bullet"),
            ),
        ),)
        doc = _doc(body=(
            _list_para("L0", level=0),
            _list_para("L1", level=1),
        ), numbering=nd)
        parsed = _roundtrip(doc)
        assert parsed.body[0].list_info.level == 0
        assert parsed.body[1].list_info.level == 1

    def test_list_text_preserved(self):
        nd = (_numbering(),)
        doc = _doc(body=(_list_para("My item"),), numbering=nd)
        parsed = _roundtrip(doc)
        assert parsed.body[0].runs[0].text == "My item"

    def test_ordered_list_numbering_definition(self):
        nd = (_numbering("1", "decimal"),)
        doc = _doc(body=(_list_para("One"),), numbering=nd)
        parsed = _roundtrip(doc)
        assert len(parsed.numbering) == 1
        assert parsed.numbering[0].levels[0].num_fmt == "decimal"

    def test_bullet_list_numbering_definition(self):
        nd = (_numbering("1", "bullet"),)
        doc = _doc(body=(_list_para("Bullet"),), numbering=nd)
        parsed = _roundtrip(doc)
        assert parsed.numbering[0].levels[0].num_fmt == "bullet"

    def test_multiple_items_same_list(self):
        nd = (_numbering(),)
        doc = _doc(body=(
            _list_para("A"), _list_para("B"), _list_para("C")
        ), numbering=nd)
        parsed = _roundtrip(doc)
        assert len(parsed.body) == 3

    def test_list_followed_by_paragraph(self):
        nd = (_numbering(),)
        doc = _doc(body=(_list_para("Item"), _para("Normal")), numbering=nd)
        parsed = _roundtrip(doc)
        assert parsed.body[0].list_info is not None
        assert parsed.body[1].list_info is None

    def test_non_li_child_of_ul_ignored(self):
        # A <ul> whose first child is not a <li> — should not crash
        html = (
            '<html><body>'
            '<div class="dw-document"'
            ' data-dw-page-width="595.28pt" data-dw-page-height="841.89pt"'
            ' data-dw-margin-top="72pt" data-dw-margin-bottom="72pt"'
            ' data-dw-margin-left="72pt" data-dw-margin-right="72pt">'
            '<ul class="dw-list" data-dw-num-id="1">'
            '<span>ignored</span>'
            '<li class="dw-li" data-dw-num-id="1" data-dw-level="0">'
            '<p class="dw-p"><span class="dw-r">Item</span></p>'
            '</li>'
            '</ul>'
            '</div>'
            '</body></html>'
        )
        parsed = parse_html(html)
        assert len(parsed.body) == 1
        assert parsed.body[0].runs[0].text == "Item"


# ---------------------------------------------------------------------------
# Styles reconstruction
# ---------------------------------------------------------------------------

class TestStylesReconstruction:
    def test_style_id_collected(self):
        para = _para(style_id="Heading1")
        parsed = _roundtrip(_doc(body=(para,)))
        style_ids = {s.style_id for s in parsed.styles}
        assert "Heading1" in style_ids

    def test_no_styles_when_no_style_ids(self):
        parsed = _roundtrip(_doc(body=(_para(),)))
        assert parsed.styles == ()

    def test_duplicate_style_ids_deduplicated(self):
        doc = _doc(body=(_para(style_id="Normal"), _para(style_id="Normal")))
        parsed = _roundtrip(doc)
        assert len([s for s in parsed.styles if s.style_id == "Normal"]) == 1
