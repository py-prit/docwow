"""Tests for docwow.writer.document_writer."""
import base64
import pytest
from lxml import etree

from docwow.models.document import Document
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo
from docwow.models.paragraph import Hyperlink, ImageRun, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.models.table import Table, TableCell, TableRow
from docwow.writer.document_writer import build_document_xml


def _hyperlink_para(url="https://example.com", text="Click here"):
    link = Hyperlink(url=url, runs=(TextRun(text=text),))
    return Paragraph(runs=(link,), formatting=ParagraphFormatting())

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50


def _doc(body=(), **kw):
    kw.setdefault("styles", ())
    kw.setdefault("numbering", ())
    kw.setdefault("page_width_pt", 595.28)
    kw.setdefault("page_height_pt", 841.89)
    kw.setdefault("margin_top_pt", 72.0)
    kw.setdefault("margin_bottom_pt", 72.0)
    kw.setdefault("margin_left_pt", 72.0)
    kw.setdefault("margin_right_pt", 72.0)
    return Document(body=body, **kw)


def _para(text="Hello", list_info=None, **fmt_kw):
    fmt = ParagraphFormatting(**fmt_kw)
    return Paragraph(runs=(TextRun(text=text),), formatting=fmt, list_info=list_info)


def _run_para(**run_kw):
    run = TextRun(text="x", formatting=RunFormatting(**run_kw))
    return Paragraph(runs=(run,), formatting=ParagraphFormatting())


def _img_para(rid="rId1"):
    img = InlineImage(
        relationship_id=rid, content_type="image/png",
        data=PNG, width_pt=72.0, height_pt=36.0,
    )
    return Paragraph(runs=(ImageRun(image=img),), formatting=ParagraphFormatting())


def _xml(doc, image_rids=None, hyperlink_rids=None) -> str:
    return build_document_xml(doc, image_rids or {}, hyperlink_rids or {}).decode("utf-8")


def _root(doc, image_rids=None, hyperlink_rids=None) -> etree._Element:
    return etree.fromstring(build_document_xml(doc, image_rids or {}, hyperlink_rids or {}))


# ---------------------------------------------------------------------------
# Document structure
# ---------------------------------------------------------------------------

class TestDocumentStructure:
    def test_returns_bytes(self):
        assert isinstance(build_document_xml(_doc(), {}), bytes)

    def test_xml_declaration(self):
        assert _xml(_doc()).startswith("<?xml")

    def test_root_is_document(self):
        assert "document" in _root(_doc()).tag

    def test_body_element_present(self):
        assert "body" in _xml(_doc())

    def test_sect_pr_present(self):
        assert "sectPr" in _xml(_doc())

    def test_page_size_twips(self):
        # 595.28pt → 11906 twips (round)
        xml = _xml(_doc())
        assert "11906" in xml

    def test_margin_twips(self):
        # 72pt → 1440 twips
        assert "1440" in _xml(_doc())


# ---------------------------------------------------------------------------
# Paragraph
# ---------------------------------------------------------------------------

class TestParagraphWriting:
    def test_p_element_emitted(self):
        assert "<w:p>" in _xml(_doc(body=(_para(),)))

    def test_pPr_present(self):
        assert "pPr" in _xml(_doc(body=(_para(),)))

    def test_style_id(self):
        doc = _doc(body=(Paragraph(
            runs=(TextRun(text="x"),),
            formatting=ParagraphFormatting(style_id="Heading1"),
        ),))
        assert "Heading1" in _xml(doc)

    def test_alignment(self):
        assert "center" in _xml(_doc(body=(_para(alignment="center"),)))

    def test_justify_becomes_both(self):
        assert "both" in _xml(_doc(body=(_para(alignment="justify"),)))

    def test_indent_left(self):
        assert "720" in _xml(_doc(body=(_para(indent_left_pt=36.0),)))

    def test_indent_right(self):
        assert "360" in _xml(_doc(body=(_para(indent_right_pt=18.0),)))

    def test_first_line_indent(self):
        xml = _xml(_doc(body=(_para(indent_first_line_pt=18.0),)))
        assert "firstLine" in xml

    def test_hanging_indent(self):
        xml = _xml(_doc(body=(_para(indent_first_line_pt=-18.0),)))
        assert "hanging" in xml

    def test_space_before(self):
        assert "240" in _xml(_doc(body=(_para(space_before_pt=12.0),)))

    def test_space_after(self):
        assert "160" in _xml(_doc(body=(_para(space_after_pt=8.0),)))

    def test_line_spacing(self):
        xml = _xml(_doc(body=(_para(line_spacing_pt=14.0),)))
        assert "280" in xml
        assert "exact" in xml

    def test_keep_together(self):
        assert "keepLines" in _xml(_doc(body=(_para(keep_together=True),)))

    def test_keep_with_next(self):
        assert "keepNext" in _xml(_doc(body=(_para(keep_with_next=True),)))

    def test_page_break_before(self):
        assert "pageBreakBefore" in _xml(_doc(body=(_para(page_break_before=True),)))

    def test_list_info_written(self):
        para = _para(list_info=ListInfo(num_id="2", level=1))
        xml = _xml(_doc(body=(para,)))
        assert "numPr" in xml
        assert '"2"' in xml
        assert '"1"' in xml

    def test_empty_paragraph(self):
        p = Paragraph(runs=(), formatting=ParagraphFormatting())
        assert "w:p" in _xml(_doc(body=(p,)))


# ---------------------------------------------------------------------------
# Text run
# ---------------------------------------------------------------------------

class TestTextRunWriting:
    def test_w_r_element(self):
        assert "<w:r>" in _xml(_doc(body=(_para("Hello"),)))

    def test_w_t_element(self):
        assert "<w:t" in _xml(_doc(body=(_para("Hello"),)))

    def test_text_content(self):
        assert "Hello" in _xml(_doc(body=(_para("Hello"),)))

    def test_xml_space_preserve(self):
        assert 'xml:space="preserve"' in _xml(_doc(body=(_para("Hello"),)))

    def test_special_chars_escaped(self):
        para = Paragraph(
            runs=(TextRun(text="a&b<c>d"),),
            formatting=ParagraphFormatting(),
        )
        xml = _xml(_doc(body=(para,)))
        assert "&amp;" in xml
        assert "&lt;" in xml
        assert "&gt;" in xml

    def test_newline_becomes_br(self):
        para = Paragraph(
            runs=(TextRun(text="line1\nline2"),),
            formatting=ParagraphFormatting(),
        )
        xml = _xml(_doc(body=(para,)))
        assert "<w:br" in xml
        assert "line1" in xml
        assert "line2" in xml

    def test_no_rPr_for_default_formatting(self):
        # Default TextRun formatting → no <w:rPr> inside the run
        xml = _xml(_doc(body=(_para("x"),)))
        assert "<w:r>" in xml   # bare <w:r> with no attributes confirms no rPr
        assert "<w:rPr" not in xml

    def test_bold_in_rPr(self):
        assert "<w:b" in _xml(_doc(body=(_run_para(bold=True),)))

    def test_italic_in_rPr(self):
        assert "<w:i" in _xml(_doc(body=(_run_para(italic=True),)))

    def test_underline_in_rPr(self):
        assert "single" in _xml(_doc(body=(_run_para(underline=True),)))

    def test_strike_in_rPr(self):
        assert "strike" in _xml(_doc(body=(_run_para(strike=True),)))

    def test_font_name(self):
        assert "Arial" in _xml(_doc(body=(_run_para(font_name="Arial"),)))

    def test_font_size(self):
        # 14pt = 28 half-points
        assert "28" in _xml(_doc(body=(_run_para(font_size_pt=14.0),)))

    def test_color(self):
        assert "FF0000" in _xml(_doc(body=(_run_para(color="FF0000"),)))

    def test_highlight(self):
        assert "yellow" in _xml(_doc(body=(_run_para(highlight="yellow"),)))

    def test_superscript(self):
        assert "superscript" in _xml(_doc(body=(_run_para(vertical_align="superscript"),)))

    def test_subscript(self):
        assert "subscript" in _xml(_doc(body=(_run_para(vertical_align="subscript"),)))


# ---------------------------------------------------------------------------
# Image run
# ---------------------------------------------------------------------------

class TestImageRunWriting:
    def test_drawing_element_present(self):
        doc = _doc(body=(_img_para(),))
        assert "drawing" in _xml(doc, {"rId1": "rId1"})

    def test_blip_embed_uses_mapped_rid(self):
        doc = _doc(body=(_img_para("orig"),))
        xml = _xml(doc, {"orig": "rId42"})
        assert "rId42" in xml

    def test_image_dimensions_in_emu(self):
        # 72pt width → 914400 EMU
        doc = _doc(body=(_img_para(),))
        xml = _xml(doc, {"rId1": "rId1"})
        assert "914400" in xml   # width
        assert "457200" in xml   # height 36pt

    def test_multiple_images_increment_draw_id(self):
        img1 = InlineImage("rId1", "image/png", PNG, 72.0, 36.0)
        img2 = InlineImage("rId2", "image/png", PNG, 72.0, 36.0)
        para1 = Paragraph(runs=(ImageRun(img1),), formatting=ParagraphFormatting())
        para2 = Paragraph(runs=(ImageRun(img2),), formatting=ParagraphFormatting())
        doc = _doc(body=(para1, para2))
        xml = _xml(doc, {"rId1": "rId1", "rId2": "rId2"})
        assert 'id="1"' in xml
        assert 'id="2"' in xml


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

class TestTableWriting:
    def _simple_table(self, text="cell", **table_kw):
        p = _para(text)
        cell = TableCell(paragraphs=(p,))
        row = TableRow(cells=(cell,))
        return Table(rows=(row,), **table_kw)

    def test_tbl_element(self):
        assert "<w:tbl>" in _xml(_doc(body=(self._simple_table(),)))

    def test_tblPr_present(self):
        assert "tblPr" in _xml(_doc(body=(self._simple_table(),)))

    def test_style_id(self):
        t = self._simple_table(style_id="TableGrid")
        assert "TableGrid" in _xml(_doc(body=(t,)))

    def test_no_style_id_when_none(self):
        assert "tblStyle" not in _xml(_doc(body=(self._simple_table(),)))

    def test_table_width(self):
        t = self._simple_table(width_pt=451.0)
        # 451 * 20 = 9020 twips
        assert "9020" in _xml(_doc(body=(t,)))

    def test_col_widths(self):
        t = Table(
            rows=(TableRow(cells=(TableCell(paragraphs=(_para(),)),)),),
            col_widths_pt=(100.0,),
        )
        assert "2000" in _xml(_doc(body=(t,)))   # 100 * 20

    def test_borders_present(self):
        assert "tblBorders" in _xml(_doc(body=(self._simple_table(),)))

    def test_tr_element(self):
        assert "<w:tr>" in _xml(_doc(body=(self._simple_table(),)))

    def test_row_height(self):
        row = TableRow(cells=(TableCell(paragraphs=(_para(),)),), height_pt=28.0)
        t = Table(rows=(row,))
        assert "560" in _xml(_doc(body=(t,)))   # 28 * 20

    def test_no_height_when_none(self):
        assert "trHeight" not in _xml(_doc(body=(self._simple_table(),)))

    def test_td_element(self):
        assert "<w:tc>" in _xml(_doc(body=(self._simple_table(),)))

    def test_cell_text(self):
        assert "cell" in _xml(_doc(body=(self._simple_table("cell"),)))

    def test_col_span(self):
        cell = TableCell(paragraphs=(_para(),), col_span=3)
        t = Table(rows=(TableRow(cells=(cell,)),))
        assert "gridSpan" in _xml(_doc(body=(t,)))
        assert '"3"' in _xml(_doc(body=(t,)))

    def test_no_gridspan_when_one(self):
        assert "gridSpan" not in _xml(_doc(body=(self._simple_table(),)))

    def test_cell_width(self):
        cell = TableCell(paragraphs=(_para(),), width_pt=144.0)
        t = Table(rows=(TableRow(cells=(cell,)),))
        assert "2880" in _xml(_doc(body=(t,)))   # 144 * 20

    def test_v_merge_start(self):
        cell = TableCell(paragraphs=(_para(),), v_merge_start=True)
        t = Table(rows=(TableRow(cells=(cell,)),))
        xml = _xml(_doc(body=(t,)))
        assert "vMerge" in xml
        assert "restart" in xml

    def test_v_merge_continue(self):
        cell = TableCell(paragraphs=(_para(),), v_merge_continue=True)
        t = Table(rows=(TableRow(cells=(cell,)),))
        xml = _xml(_doc(body=(t,)))
        assert "vMerge" in xml
        assert "restart" not in xml

    def test_empty_cell_gets_empty_paragraph(self):
        cell = TableCell(paragraphs=())
        t = Table(rows=(TableRow(cells=(cell,)),))
        xml = _xml(_doc(body=(t,)))
        assert "<w:tc>" in xml
        assert "<w:p" in xml


# ---------------------------------------------------------------------------
# Hyperlink
# ---------------------------------------------------------------------------

class TestHyperlinkWriting:
    def test_hyperlink_element_present(self):
        doc = _doc(body=(_hyperlink_para(),))
        xml = _xml(doc, hyperlink_rids={"https://example.com": "rId10"})
        assert "hyperlink" in xml

    def test_hyperlink_rid_in_output(self):
        doc = _doc(body=(_hyperlink_para(),))
        xml = _xml(doc, hyperlink_rids={"https://example.com": "rId10"})
        assert "rId10" in xml

    def test_hyperlink_text_in_output(self):
        doc = _doc(body=(_hyperlink_para(text="Go here"),))
        xml = _xml(doc, hyperlink_rids={"https://example.com": "rId10"})
        assert "Go here" in xml

    def test_hyperlink_run_inside_hyperlink(self):
        doc = _doc(body=(_hyperlink_para(),))
        xml = _xml(doc, hyperlink_rids={"https://example.com": "rId1"})
        # <w:r> must appear (inside the hyperlink element)
        assert "<w:r>" in xml

    def test_hyperlink_no_rids_emits_empty_rid(self):
        # No rids map provided → rid attribute should be empty string (not crash)
        doc = _doc(body=(_hyperlink_para(),))
        xml = _xml(doc)
        assert "hyperlink" in xml

    def test_multiple_hyperlinks_get_different_rids(self):
        link1 = Hyperlink(url="https://a.com", runs=(TextRun(text="A"),))
        link2 = Hyperlink(url="https://b.com", runs=(TextRun(text="B"),))
        para = Paragraph(runs=(link1, link2), formatting=ParagraphFormatting())
        doc = _doc(body=(para,))
        xml = _xml(doc, hyperlink_rids={"https://a.com": "rId2", "https://b.com": "rId3"})
        assert "rId2" in xml
        assert "rId3" in xml

    def test_hyperlink_with_multiple_inner_runs(self):
        link = Hyperlink(url="https://example.com", runs=(
            TextRun(text="Hello "), TextRun(text="world"),
        ))
        para = Paragraph(runs=(link,), formatting=ParagraphFormatting())
        doc = _doc(body=(para,))
        xml = _xml(doc, hyperlink_rids={"https://example.com": "rId1"})
        assert "Hello " in xml
        assert "world" in xml

    def test_hyperlink_mixed_with_text_run(self):
        link = Hyperlink(url="https://example.com", runs=(TextRun(text="link"),))
        para = Paragraph(
            runs=(TextRun(text="See "), link, TextRun(text=" here")),
            formatting=ParagraphFormatting(),
        )
        doc = _doc(body=(para,))
        xml = _xml(doc, hyperlink_rids={"https://example.com": "rId1"})
        assert "See " in xml
        assert "link" in xml
        assert " here" in xml

    def test_anchor_hyperlink_uses_w_anchor(self):
        link = Hyperlink(url="#section1", runs=(TextRun(text="go"),))
        para = Paragraph(runs=(link,), formatting=ParagraphFormatting())
        doc = _doc(body=(para,))
        xml = _xml(doc)
        assert 'w:anchor="section1"' in xml

    def test_anchor_hyperlink_no_r_id(self):
        link = Hyperlink(url="#section1", runs=(TextRun(text="go"),))
        para = Paragraph(runs=(link,), formatting=ParagraphFormatting())
        doc = _doc(body=(para,))
        xml = _xml(doc)
        assert 'r:id' not in xml

    def test_anchor_hyperlink_text_present(self):
        link = Hyperlink(url="#intro", runs=(TextRun(text="Introduction"),))
        para = Paragraph(runs=(link,), formatting=ParagraphFormatting())
        doc = _doc(body=(para,))
        xml = _xml(doc)
        assert "Introduction" in xml
