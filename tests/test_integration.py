"""
Integration and round-trip tests for docwow.

Three tiers of confidence:
  1. DOCX → parse → HTML → parse → compare body formatting
  2. DOCX → to_html() → to_docx() → re-parse — verify valid DOCX structure
  3. Public API smoke tests (open / to_html / to_docx)
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

import docwow
from docwow.models.document import Document
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import ImageRun, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.models.table import Table, TableCell, TableRow

FIXTURES = Path(__file__).parent / "fixtures"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc(body=(), styles=(), numbering=()):
    return Document(
        body=body, styles=styles, numbering=numbering,
        page_width_pt=595.28, page_height_pt=841.89,
        margin_top_pt=72.0, margin_bottom_pt=72.0,
        margin_left_pt=72.0, margin_right_pt=72.0,
    )


def _para(text="Hello", **fmt_kw):
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(**fmt_kw),
    )


def _roundtrip_model(doc: Document) -> Document:
    """DOCX bytes → re-parsed Document (via write_docx → parse_docx)."""
    data = docwow.write_docx(doc)
    return docwow.parse_docx(data)


def _roundtrip_html(doc: Document) -> Document:
    """Document → HTML → Document (render_document → parse_html)."""
    html = docwow.render_document(doc)
    return docwow.parse_html(html)


def _is_valid_zip(data: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class TestPublicApi:
    def test_open_docx_file(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        assert isinstance(doc, Document)

    def test_open_docx_bytes(self):
        data = (FIXTURES / "paragraphs.docx").read_bytes()
        doc = docwow.open(data)
        assert isinstance(doc, Document)

    def test_open_html_string(self):
        html = docwow.render_document(_doc(body=(_para("test"),)))
        doc = docwow.open(html)
        assert isinstance(doc, Document)

    def test_open_invalid_type_raises(self):
        with pytest.raises(TypeError):
            docwow.open(12345)

    def test_to_html_returns_string(self):
        html = docwow.to_html(FIXTURES / "paragraphs.docx")
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_to_html_contains_text(self):
        html = docwow.to_html(FIXTURES / "paragraphs.docx")
        assert len(html) > 100

    def test_to_docx_returns_bytes(self):
        html = docwow.render_document(_doc(body=(_para("hello"),)))
        data = docwow.to_docx(html)
        assert isinstance(data, bytes)
        assert _is_valid_zip(data)

    def test_to_docx_bytes_input(self):
        html = docwow.render_document(_doc(body=(_para("hello"),)))
        data = docwow.to_docx(html.encode("utf-8"))
        assert _is_valid_zip(data)

    def test_to_docx_writes_file(self, tmp_path):
        html = docwow.render_document(_doc(body=(_para("hello"),)))
        out = tmp_path / "result.docx"
        data = docwow.to_docx(html, target=str(out))
        assert out.exists()
        assert out.read_bytes() == data

    def test_version_string_exists(self):
        assert hasattr(docwow, "__version__")
        assert isinstance(docwow.__version__, str)


# ---------------------------------------------------------------------------
# Fixture DOCX files — parse produces a valid Document
# ---------------------------------------------------------------------------

class TestFixtureParsing:
    @pytest.mark.parametrize("filename", [
        "empty.docx",
        "paragraphs.docx",
        "formatting.docx",
        "table_simple.docx",
        "table_merged.docx",
        "list_bullet.docx",
        "list_numbered.docx",
        "list_nested.docx",
        "image_inline.docx",
        "mixed.docx",
    ])
    def test_fixture_parses_without_error(self, filename):
        doc = docwow.parse_docx(FIXTURES / filename)
        assert isinstance(doc, Document)

    @pytest.mark.parametrize("filename", [
        "empty.docx",
        "paragraphs.docx",
        "formatting.docx",
        "table_simple.docx",
        "table_merged.docx",
        "list_bullet.docx",
        "list_numbered.docx",
        "list_nested.docx",
        "image_inline.docx",
        "mixed.docx",
    ])
    def test_fixture_renders_to_html(self, filename):
        doc = docwow.parse_docx(FIXTURES / filename)
        html = docwow.render_document(doc)
        assert "<!DOCTYPE html>" in html
        assert "dw-document" in html

    @pytest.mark.parametrize("filename", [
        "empty.docx",
        "paragraphs.docx",
        "formatting.docx",
        "table_simple.docx",
        "list_bullet.docx",
        "list_numbered.docx",
        "image_inline.docx",
        "mixed.docx",
    ])
    def test_fixture_full_pipeline_produces_valid_docx(self, filename):
        """DOCX → HTML → DOCX: final output must be a valid ZIP."""
        html = docwow.to_html(FIXTURES / filename)
        data = docwow.to_docx(html)
        assert _is_valid_zip(data)

    def test_paragraphs_fixture_body_non_empty(self):
        doc = docwow.parse_docx(FIXTURES / "paragraphs.docx")
        assert len(doc.body) > 0

    def test_formatting_fixture_has_run_formatting(self):
        doc = docwow.parse_docx(FIXTURES / "formatting.docx")
        all_runs = [
            run for el in doc.body
            if isinstance(el, Paragraph)
            for run in el.runs
            if isinstance(run, TextRun)
        ]
        has_formatting = any(
            r.formatting.bold or r.formatting.italic or r.formatting.font_size_pt
            for r in all_runs
        )
        assert has_formatting

    def test_table_fixture_has_table(self):
        doc = docwow.parse_docx(FIXTURES / "table_simple.docx")
        tables = [el for el in doc.body if isinstance(el, Table)]
        assert len(tables) > 0

    def test_list_fixture_has_list_paragraphs(self):
        doc = docwow.parse_docx(FIXTURES / "list_bullet.docx")
        list_paras = [
            el for el in doc.body
            if isinstance(el, Paragraph) and el.list_info is not None
        ]
        assert len(list_paras) > 0

    def test_image_fixture_has_image(self):
        doc = docwow.parse_docx(FIXTURES / "image_inline.docx")
        images = [
            run for el in doc.body
            if isinstance(el, Paragraph)
            for run in el.runs
            if isinstance(run, ImageRun)
        ]
        assert len(images) > 0
        assert images[0].image.data != b""


# ---------------------------------------------------------------------------
# HTML round-trip: Document → HTML → Document (body formatting preserved)
# ---------------------------------------------------------------------------

class TestHtmlRoundTrip:
    def test_empty_document(self):
        doc = _doc()
        rt = _roundtrip_html(doc)
        assert rt.body == ()

    def test_page_geometry(self):
        doc = _doc()
        rt = _roundtrip_html(doc)
        assert rt.page_width_pt == 595.28
        assert rt.margin_top_pt == 72.0

    def test_paragraph_text(self):
        doc = _doc(body=(_para("Round trip"),))
        rt = _roundtrip_html(doc)
        assert rt.body[0].runs[0].text == "Round trip"

    def test_paragraph_alignment(self):
        doc = _doc(body=(_para(alignment="center"),))
        rt = _roundtrip_html(doc)
        assert rt.body[0].formatting.alignment == "center"

    def test_paragraph_indent(self):
        doc = _doc(body=(_para(indent_left_pt=36.0),))
        rt = _roundtrip_html(doc)
        assert rt.body[0].formatting.indent_left_pt == 36.0

    def test_run_bold(self):
        run = TextRun(text="bold", formatting=RunFormatting(bold=True))
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        rt = _roundtrip_html(_doc(body=(para,)))
        assert rt.body[0].runs[0].formatting.bold is True

    def test_run_font_name(self):
        run = TextRun(text="x", formatting=RunFormatting(font_name="Arial"))
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        rt = _roundtrip_html(_doc(body=(para,)))
        assert rt.body[0].runs[0].formatting.font_name == "Arial"

    def test_run_color(self):
        run = TextRun(text="x", formatting=RunFormatting(color="FF0000"))
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        rt = _roundtrip_html(_doc(body=(para,)))
        assert rt.body[0].runs[0].formatting.color == "FF0000"

    def test_image_run(self):
        img = InlineImage("rId1", "image/png", PNG, 72.0, 36.0)
        para = Paragraph(runs=(ImageRun(image=img),), formatting=ParagraphFormatting())
        rt = _roundtrip_html(_doc(body=(para,)))
        result_img = rt.body[0].runs[0].image
        assert result_img.data == PNG
        assert result_img.width_pt == 72.0

    def test_list_info(self):
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        ),)
        para = Paragraph(
            runs=(TextRun(text="item"),),
            formatting=ParagraphFormatting(),
            list_info=ListInfo(num_id="1", level=0),
        )
        rt = _roundtrip_html(_doc(body=(para,), numbering=nd))
        assert rt.body[0].list_info is not None
        assert rt.body[0].list_info.level == 0

    def test_table(self):
        p = _para("cell text")
        cell = TableCell(paragraphs=(p,))
        row = TableRow(cells=(cell,))
        table = Table(rows=(row,))
        rt = _roundtrip_html(_doc(body=(table,)))
        assert isinstance(rt.body[0], Table)
        assert rt.body[0].rows[0].cells[0].paragraphs[0].runs[0].text == "cell text"

    def test_mixed_body_order_preserved(self):
        table = Table(rows=(TableRow(cells=(TableCell(paragraphs=(_para("t"),)),)),))
        doc = _doc(body=(_para("first"), table, _para("last")))
        rt = _roundtrip_html(doc)
        assert isinstance(rt.body[0], Paragraph)
        assert isinstance(rt.body[1], Table)
        assert isinstance(rt.body[2], Paragraph)


# ---------------------------------------------------------------------------
# DOCX round-trip: Document → write_docx → parse_docx (structure preserved)
# ---------------------------------------------------------------------------

class TestDocxRoundTrip:
    def test_empty_document_roundtrip(self):
        doc = _doc()
        rt = _roundtrip_model(doc)
        assert isinstance(rt, Document)
        assert rt.body == ()

    def test_page_geometry_preserved(self):
        doc = _doc()
        rt = _roundtrip_model(doc)
        assert abs(rt.page_width_pt - 595.28) < 0.5
        assert abs(rt.margin_top_pt - 72.0) < 0.5

    def test_paragraph_text_preserved(self):
        doc = _doc(body=(_para("Hello DOCX round-trip"),))
        rt = _roundtrip_model(doc)
        assert len(rt.body) == 1
        assert isinstance(rt.body[0], Paragraph)
        texts = [r.text for r in rt.body[0].runs if isinstance(r, TextRun)]
        assert "Hello DOCX round-trip" in texts

    def test_bold_run_preserved(self):
        run = TextRun(text="bold", formatting=RunFormatting(bold=True))
        para = Paragraph(runs=(run,), formatting=ParagraphFormatting())
        rt = _roundtrip_model(_doc(body=(para,)))
        assert any(r.formatting.bold for r in rt.body[0].runs if isinstance(r, TextRun))

    def test_table_preserved(self):
        p = _para("cell")
        cell = TableCell(paragraphs=(p,))
        row = TableRow(cells=(cell,))
        table = Table(rows=(row,))
        rt = _roundtrip_model(_doc(body=(table,)))
        tables = [el for el in rt.body if isinstance(el, Table)]
        assert len(tables) == 1

    def test_list_paragraph_preserved(self):
        nd = (NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        ),)
        para = Paragraph(
            runs=(TextRun(text="item"),),
            formatting=ParagraphFormatting(),
            list_info=ListInfo(num_id="1", level=0),
        )
        rt = _roundtrip_model(_doc(body=(para,), numbering=nd))
        list_paras = [el for el in rt.body if isinstance(el, Paragraph) and el.list_info]
        assert len(list_paras) > 0

    def test_image_preserved(self):
        img = InlineImage("rId1", "image/png", PNG, 72.0, 36.0)
        para = Paragraph(runs=(ImageRun(image=img),), formatting=ParagraphFormatting())
        rt = _roundtrip_model(_doc(body=(para,)))
        images = [
            run for el in rt.body if isinstance(el, Paragraph)
            for run in el.runs if isinstance(run, ImageRun)
        ]
        assert len(images) == 1
        assert images[0].image.data == PNG

    def test_multiple_paragraphs_count(self):
        doc = _doc(body=(_para("A"), _para("B"), _para("C")))
        rt = _roundtrip_model(doc)
        paras = [el for el in rt.body if isinstance(el, Paragraph)]
        assert len(paras) == 3

    def test_output_is_valid_zip(self):
        data = docwow.write_docx(_doc(body=(_para("test"),)))
        assert _is_valid_zip(data)

    def test_output_contains_required_parts(self):
        data = docwow.write_docx(_doc(body=(_para("test"),)))
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = set(zf.namelist())
        required = {
            "[Content_Types].xml",
            "_rels/.rels",
            "word/document.xml",
            "word/styles.xml",
            "word/settings.xml",
        }
        assert required.issubset(names)
