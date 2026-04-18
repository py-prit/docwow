"""Tests for section break writing."""

from __future__ import annotations

import io
import zipfile

import docwow
from lxml import etree

from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.section import SectionBreak, SectionProperties
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.writer.document_writer import _write_section_break

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _qn(name: str) -> str:
    return f"{{{W}}}{name}"


def _write(props: SectionProperties) -> etree._Element:
    parent = etree.Element(_qn("body"))
    _write_section_break(parent, props)
    return parent


class TestSectionBreakWriter:
    def test_writes_empty_paragraph(self):
        parent = _write(SectionProperties())
        p_el = parent.find(_qn("p"))
        assert p_el is not None

    def test_ppr_contains_sectpr(self):
        parent = _write(SectionProperties())
        p_el = parent.find(_qn("p"))
        pPr = p_el.find(_qn("pPr"))
        assert pPr is not None
        sect_pr = pPr.find(_qn("sectPr"))
        assert sect_pr is not None

    def test_page_size_written(self):
        parent = _write(SectionProperties(page_width_pt=612.0, page_height_pt=792.0))
        sect_pr = parent.find(_qn("p")).find(_qn("pPr")).find(_qn("sectPr"))
        pgSz = sect_pr.find(_qn("pgSz"))
        assert pgSz is not None
        assert pgSz.get(_qn("w")) == "12240"   # 612pt = 12240 twips
        assert pgSz.get(_qn("h")) == "15840"   # 792pt = 15840 twips

    def test_margins_written(self):
        parent = _write(SectionProperties(
            margin_top_pt=36.0, margin_bottom_pt=36.0,
            margin_left_pt=54.0, margin_right_pt=54.0,
        ))
        sect_pr = parent.find(_qn("p")).find(_qn("pPr")).find(_qn("sectPr"))
        pgMar = sect_pr.find(_qn("pgMar"))
        assert pgMar is not None
        assert pgMar.get(_qn("top")) == "720"   # 36pt = 720 twips
        assert pgMar.get(_qn("left")) == "1080" # 54pt = 1080 twips

    def test_break_type_written(self):
        parent = _write(SectionProperties(break_type="continuous"))
        sect_pr = parent.find(_qn("p")).find(_qn("pPr")).find(_qn("sectPr"))
        type_el = sect_pr.find(_qn("type"))
        assert type_el is not None
        assert type_el.get(_qn("val")) == "continuous"


class TestSectionBreakRoundTrip:
    """Verify [Paragraph, SectionBreak] round-trips without gaining an extra paragraph."""

    _SECT_ATTRS = (
        'data-dw-break-type="nextPage"'
        ' data-dw-page-width="595.3pt" data-dw-page-height="841.9pt"'
        ' data-dw-margin-top="72pt" data-dw-margin-bottom="72pt"'
        ' data-dw-margin-left="72pt" data-dw-margin-right="72pt"'
    )

    def _make_html(self) -> str:
        return (
            '<div class="dw-document">'
            '<p class="dw-p"><span class="dw-r">Hello</span></p>'
            f'<div class="dw-section-break" {self._SECT_ATTRS}></div>'
            '<p class="dw-p"><span class="dw-r">World</span></p>'
            '</div>'
        )

    def _doc_xml(self, data: bytes) -> bytes:
        import io, zipfile
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return zf.read("word/document.xml")

    def test_sectpr_embedded_in_preceding_paragraph(self):
        """w:sectPr must live inside the preceding paragraph's w:pPr, not a new w:p."""
        docx = docwow.to_docx(self._make_html())
        W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        root = etree.fromstring(self._doc_xml(docx))
        body = root.find(f"{{{W_NS}}}body")
        paras = body.findall(f"{{{W_NS}}}p")
        # 2 paragraphs: "Hello" (with inline sectPr) and "World".
        # The final document sectPr is a direct w:body child, not wrapped in w:p.
        assert len(paras) == 2, f"Expected 2 <w:p> elements, got {len(paras)}"
        ppr = paras[0].find(f"{{{W_NS}}}pPr")
        assert ppr is not None
        assert ppr.find(f"{{{W_NS}}}sectPr") is not None, \
            "w:sectPr must be embedded in the preceding paragraph's w:pPr"

    def test_no_extra_paragraph_on_round_trip(self):
        """Re-opening a round-tripped DOCX must not gain extra paragraphs from section breaks."""
        doc = docwow.open(docwow.to_docx(docwow.to_html(docwow.to_docx(self._make_html()))))
        from docwow.api.paragraph import MutableParagraph, MutableSectionBreak
        body_items = list(doc.paragraphs)
        assert sum(1 for i in body_items if isinstance(i, MutableSectionBreak)) == 1
        sb_index = next(i for i, item in enumerate(body_items) if isinstance(item, MutableSectionBreak))
        assert isinstance(body_items[sb_index - 1], MutableParagraph)
        assert body_items[sb_index - 1].get_text() == "Hello"
