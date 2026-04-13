"""Tests for docwow.writer.footnote_writer."""
import zipfile
import io

import pytest
from lxml import etree

from docwow.models.footnote import Footnote
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting
from docwow.writer.footnote_writer import write_endnotes, write_footnotes
from docwow.utils.xml_utils import qn


def _para(text: str) -> Paragraph:
    return Paragraph(runs=(TextRun(text=text),), formatting=ParagraphFormatting())


def _note(note_id: int, text: str, note_type: str = "footnote") -> Footnote:
    return Footnote(
        note_id=note_id,
        paragraphs=(_para(text),),
        note_type=note_type,
    )


def _parse(xml_bytes: bytes) -> etree._Element:
    return etree.fromstring(xml_bytes)


class TestWriteFootnotes:
    def test_returns_bytes(self):
        assert isinstance(write_footnotes(()), bytes)

    def test_root_tag_is_footnotes(self):
        root = _parse(write_footnotes(()))
        assert root.tag == qn("w:footnotes")

    def test_empty_has_separator_pseudo_notes(self):
        root = _parse(write_footnotes(()))
        ids = [int(el.get(qn("w:id"))) for el in root if el.tag == qn("w:footnote")]
        assert -1 in ids
        assert 0 in ids

    def test_note_appears_in_output(self):
        root = _parse(write_footnotes((_note(1, "Hello footnote"),)))
        ids = [int(el.get(qn("w:id"))) for el in root if el.tag == qn("w:footnote")]
        assert 1 in ids

    def test_note_text_content(self):
        xml = write_footnotes((_note(1, "Hello footnote"),))
        assert b"Hello footnote" in xml

    def test_multiple_notes(self):
        root = _parse(write_footnotes((_note(1, "one"), _note(2, "two"))))
        ids = [
            int(el.get(qn("w:id")))
            for el in root
            if el.tag == qn("w:footnote") and int(el.get(qn("w:id"))) > 0
        ]
        assert sorted(ids) == [1, 2]

    def test_separator_has_separator_type(self):
        root = _parse(write_footnotes(()))
        sep = next(
            el for el in root
            if el.tag == qn("w:footnote") and el.get(qn("w:id")) == "-1"
        )
        assert sep.get(qn("w:type")) == "separator"

    def test_continuation_separator_type(self):
        root = _parse(write_footnotes(()))
        sep = next(
            el for el in root
            if el.tag == qn("w:footnote") and el.get(qn("w:id")) == "0"
        )
        assert sep.get(qn("w:type")) == "continuationSeparator"

    def test_note_has_paragraph(self):
        root = _parse(write_footnotes((_note(1, "text"),)))
        note_el = next(
            el for el in root
            if el.tag == qn("w:footnote") and el.get(qn("w:id")) == "1"
        )
        paras = [c for c in note_el if c.tag == qn("w:p")]
        assert len(paras) >= 1

    def test_note_has_marker_run(self):
        xml = write_footnotes((_note(1, "text"),))
        # The marker run contains w:footnoteRef
        assert b"footnoteRef" in xml


class TestWriteEndnotes:
    def test_returns_bytes(self):
        assert isinstance(write_endnotes(()), bytes)

    def test_root_tag_is_endnotes(self):
        root = _parse(write_endnotes(()))
        assert root.tag == qn("w:endnotes")

    def test_empty_has_separator_pseudo_notes(self):
        root = _parse(write_endnotes(()))
        ids = [int(el.get(qn("w:id"))) for el in root if el.tag == qn("w:endnote")]
        assert -1 in ids
        assert 0 in ids

    def test_endnote_appears(self):
        root = _parse(write_endnotes((_note(1, "endnote text", "endnote"),)))
        ids = [int(el.get(qn("w:id"))) for el in root if el.tag == qn("w:endnote")]
        assert 1 in ids

    def test_endnote_text_content(self):
        xml = write_endnotes((_note(1, "endnote text", "endnote"),))
        assert b"endnote text" in xml

    def test_note_has_endnote_ref_marker(self):
        xml = write_endnotes((_note(1, "text", "endnote"),))
        assert b"endnoteRef" in xml


class TestDocxWriterIncludesFootnotes:
    """Integration: verify footnotes.xml and endnotes.xml appear in the written DOCX."""

    def _make_doc(self, footnotes=(), endnotes=()):
        from docwow.models.document import Document
        return Document(
            body=(), styles=(), numbering=(),
            page_width_pt=595.28, page_height_pt=841.89,
            margin_top_pt=72.0, margin_bottom_pt=72.0,
            margin_left_pt=72.0, margin_right_pt=72.0,
            footnotes=footnotes,
            endnotes=endnotes,
        )

    def test_footnotes_xml_in_zip(self):
        from docwow.writer.docx_writer import write_docx
        doc = self._make_doc(footnotes=(_note(1, "A footnote"),))
        data = write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert "word/footnotes.xml" in zf.namelist()

    def test_endnotes_xml_in_zip(self):
        from docwow.writer.docx_writer import write_docx
        doc = self._make_doc(endnotes=(_note(1, "An endnote", "endnote"),))
        data = write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert "word/endnotes.xml" in zf.namelist()

    def test_no_footnotes_xml_when_empty(self):
        from docwow.writer.docx_writer import write_docx
        doc = self._make_doc()
        data = write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert "word/footnotes.xml" not in zf.namelist()
