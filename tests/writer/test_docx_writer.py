"""Tests for docwow.writer.docx_writer — integration-level ZIP verification."""
import io
import zipfile
import tempfile
from pathlib import Path

import pytest
from lxml import etree

from docwow.models.document import Document
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import ImageRun, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.models.table import Table, TableCell, TableRow
from docwow.writer.docx_writer import write_docx, _collect_images

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 50


def _doc(body=(), styles=(), numbering=()):
    return Document(
        body=body, styles=styles, numbering=numbering,
        page_width_pt=595.28, page_height_pt=841.89,
        margin_top_pt=72.0, margin_bottom_pt=72.0,
        margin_left_pt=72.0, margin_right_pt=72.0,
    )


def _para(text="Hello"):
    return Paragraph(runs=(TextRun(text=text),), formatting=ParagraphFormatting())


def _list_para(text, num_id="1", level=0):
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(),
        list_info=ListInfo(num_id=num_id, level=level),
    )


def _img_para(rid="rId1", ct="image/png", data=None):
    img = InlineImage(
        relationship_id=rid, content_type=ct,
        data=data or PNG, width_pt=72.0, height_pt=36.0,
    )
    return Paragraph(runs=(ImageRun(image=img),), formatting=ParagraphFormatting())


def _nd(num_id="1", num_fmt="bullet"):
    return NumberingDefinition(
        abstract_num_id=num_id,
        levels=(ListLevel(level=0, num_fmt=num_fmt),),
    )


def _open_zip(data: bytes) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(data))


def _read_xml(data: bytes, path: str) -> etree._Element:
    with _open_zip(data) as zf:
        return etree.fromstring(zf.read(path))


# ---------------------------------------------------------------------------
# Return type and target
# ---------------------------------------------------------------------------

class TestWriteDocxBasics:
    def test_returns_bytes(self):
        assert isinstance(write_docx(_doc()), bytes)

    def test_non_empty_output(self):
        assert len(write_docx(_doc())) > 0

    def test_valid_zip(self):
        data = write_docx(_doc())
        assert zipfile.is_zipfile(io.BytesIO(data))

    def test_writes_to_file_when_target_given(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "out.docx"
            data = write_docx(_doc(), target=str(path))
            assert path.exists()
            assert path.read_bytes() == data

    def test_returns_bytes_even_with_target(self):
        with tempfile.TemporaryDirectory() as td:
            result = write_docx(_doc(), target=str(Path(td) / "out.docx"))
            assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# ZIP contents — required files always present
# ---------------------------------------------------------------------------

class TestZipContents:
    def _names(self, doc=None):
        return set(_open_zip(write_docx(doc or _doc())).namelist())

    def test_content_types_present(self):
        assert "[Content_Types].xml" in self._names()

    def test_root_rels_present(self):
        assert "_rels/.rels" in self._names()

    def test_document_xml_present(self):
        assert "word/document.xml" in self._names()

    def test_document_rels_present(self):
        assert "word/_rels/document.xml.rels" in self._names()

    def test_styles_xml_present(self):
        assert "word/styles.xml" in self._names()

    def test_settings_xml_present(self):
        assert "word/settings.xml" in self._names()

    def test_numbering_xml_absent_when_no_lists(self):
        assert "word/numbering.xml" not in self._names()

    def test_numbering_xml_present_when_lists_exist(self):
        doc = _doc(body=(_list_para("item"),), numbering=(_nd(),))
        assert "word/numbering.xml" in self._names(doc)

    def test_image_file_present(self):
        doc = _doc(body=(_img_para(),))
        assert "word/media/image1.png" in self._names(doc)

    def test_jpeg_image_gets_jpg_extension(self):
        doc = _doc(body=(_img_para(ct="image/jpeg", data=JPG),))
        names = self._names(doc)
        assert any(n.endswith(".jpg") for n in names)

    def test_two_images_two_media_files(self):
        para1 = _img_para(rid="rId1")
        para2 = _img_para(rid="rId2")
        doc = _doc(body=(para1, para2))
        names = self._names(doc)
        assert "word/media/image1.png" in names
        assert "word/media/image2.png" in names

    def test_duplicate_image_rids_deduplicated(self):
        # Same rid → same image, stored once
        para1 = _img_para(rid="rId1")
        para2 = _img_para(rid="rId1")
        doc = _doc(body=(para1, para2))
        names = self._names(doc)
        media = [n for n in names if n.startswith("word/media/")]
        assert len(media) == 1


# ---------------------------------------------------------------------------
# XML content spot-checks
# ---------------------------------------------------------------------------

class TestXmlContent:
    def test_document_xml_parseable(self):
        data = write_docx(_doc(body=(_para("Hello"),)))
        root = _read_xml(data, "word/document.xml")
        assert root is not None

    def test_paragraph_text_in_document_xml(self):
        data = write_docx(_doc(body=(_para("TestContent"),)))
        with _open_zip(data) as zf:
            xml = zf.read("word/document.xml").decode("utf-8")
        assert "TestContent" in xml

    def test_styles_xml_parseable(self):
        data = write_docx(_doc())
        root = _read_xml(data, "word/styles.xml")
        assert root is not None

    def test_numbering_xml_parseable(self):
        doc = _doc(body=(_list_para("item"),), numbering=(_nd(),))
        data = write_docx(doc)
        root = _read_xml(data, "word/numbering.xml")
        assert root is not None

    def test_image_data_stored_correctly(self):
        doc = _doc(body=(_img_para(data=PNG),))
        data = write_docx(doc)
        with _open_zip(data) as zf:
            stored = zf.read("word/media/image1.png")
        assert stored == PNG

    def test_document_rels_contains_styles(self):
        data = write_docx(_doc())
        with _open_zip(data) as zf:
            rels = zf.read("word/_rels/document.xml.rels").decode()
        assert "styles.xml" in rels

    def test_document_rels_contains_image(self):
        doc = _doc(body=(_img_para(),))
        data = write_docx(doc)
        with _open_zip(data) as zf:
            rels = zf.read("word/_rels/document.xml.rels").decode()
        assert "media/image1.png" in rels

    def test_document_rels_contains_numbering_when_lists(self):
        doc = _doc(body=(_list_para("x"),), numbering=(_nd(),))
        data = write_docx(doc)
        with _open_zip(data) as zf:
            rels = zf.read("word/_rels/document.xml.rels").decode()
        assert "numbering.xml" in rels

    def test_content_types_has_document_override(self):
        data = write_docx(_doc())
        with _open_zip(data) as zf:
            ct = zf.read("[Content_Types].xml").decode()
        assert "wordprocessingml.document.main" in ct

    def test_page_size_in_document_xml(self):
        data = write_docx(_doc())
        with _open_zip(data) as zf:
            xml = zf.read("word/document.xml").decode()
        # 595.28pt → 11906 twips
        assert "11906" in xml


# ---------------------------------------------------------------------------
# _collect_images helper
# ---------------------------------------------------------------------------

class TestCollectImages:
    def _make_img(self, rid):
        return InlineImage(
            relationship_id=rid, content_type="image/png",
            data=PNG, width_pt=72.0, height_pt=36.0,
        )

    def test_empty_body(self):
        assert _collect_images(_doc()) == []

    def test_image_in_paragraph(self):
        img = self._make_img("rId1")
        doc = _doc(body=(Paragraph(runs=(ImageRun(img),), formatting=ParagraphFormatting()),))
        assert _collect_images(doc) == [img]

    def test_no_image_in_text_only_paragraph(self):
        assert _collect_images(_doc(body=(_para(),))) == []

    def test_image_in_table_cell(self):
        img = self._make_img("rId1")
        cell = TableCell(paragraphs=(
            Paragraph(runs=(ImageRun(img),), formatting=ParagraphFormatting()),
        ))
        row = TableRow(cells=(cell,))
        table = Table(rows=(row,))
        doc = _doc(body=(table,))
        assert _collect_images(doc) == [img]

    def test_multiple_images_collected_in_order(self):
        img1 = self._make_img("rId1")
        img2 = self._make_img("rId2")
        para1 = Paragraph(runs=(ImageRun(img1),), formatting=ParagraphFormatting())
        para2 = Paragraph(runs=(ImageRun(img2),), formatting=ParagraphFormatting())
        doc = _doc(body=(para1, para2))
        result = _collect_images(doc)
        assert result == [img1, img2]
