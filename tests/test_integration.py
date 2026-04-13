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
from docwow.api.document import DocumentWrapper
from docwow.models.document import Document
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.header_footer import HeaderFooter
from docwow.models.paragraph import Hyperlink, ImageRun, PageBreak, PageNumberField, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.models.table import Table, TableCell, TableRow
from tests.fixtures.generate_showcase import build_showcase

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
        assert isinstance(doc, DocumentWrapper)

    def test_open_docx_bytes(self):
        data = (FIXTURES / "paragraphs.docx").read_bytes()
        doc = docwow.open(data)
        assert isinstance(doc, DocumentWrapper)

    def test_open_html_string(self):
        html = docwow.render_document(_doc(body=(_para("test"),)))
        doc = docwow.open(html)
        assert isinstance(doc, DocumentWrapper)

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


# ---------------------------------------------------------------------------
# Hyperlink round-trips
# ---------------------------------------------------------------------------

def _hyperlink_doc(url="https://example.com", text="Click here"):
    link = Hyperlink(url=url, runs=(TextRun(text=text),))
    para = Paragraph(runs=(link,), formatting=ParagraphFormatting())
    return _doc(body=(para,))


class TestHyperlinkHtmlRoundTrip:
    def test_hyperlink_survives_html_roundtrip(self):
        rt = _roundtrip_html(_hyperlink_doc())
        para = rt.body[0]
        assert isinstance(para, Paragraph)
        assert isinstance(para.runs[0], Hyperlink)

    def test_hyperlink_url_preserved(self):
        rt = _roundtrip_html(_hyperlink_doc(url="https://example.com"))
        assert rt.body[0].runs[0].url == "https://example.com"

    def test_hyperlink_text_preserved(self):
        rt = _roundtrip_html(_hyperlink_doc(text="Click here"))
        assert rt.body[0].runs[0].runs[0].text == "Click here"

    def test_mailto_hyperlink_preserved(self):
        rt = _roundtrip_html(_hyperlink_doc(url="mailto:hi@example.com", text="email us"))
        assert rt.body[0].runs[0].url == "mailto:hi@example.com"

    def test_multiple_hyperlinks_in_one_para(self):
        link1 = Hyperlink(url="https://a.com", runs=(TextRun(text="A"),))
        link2 = Hyperlink(url="https://b.com", runs=(TextRun(text="B"),))
        para = Paragraph(runs=(link1, link2), formatting=ParagraphFormatting())
        rt = _roundtrip_html(_doc(body=(para,)))
        assert isinstance(rt.body[0].runs[0], Hyperlink)
        assert isinstance(rt.body[0].runs[1], Hyperlink)
        assert rt.body[0].runs[0].url == "https://a.com"
        assert rt.body[0].runs[1].url == "https://b.com"

    def test_mixed_text_and_hyperlink_preserved(self):
        link = Hyperlink(url="https://example.com", runs=(TextRun(text="link"),))
        para = Paragraph(
            runs=(TextRun(text="See "), link, TextRun(text=" for info")),
            formatting=ParagraphFormatting(),
        )
        rt = _roundtrip_html(_doc(body=(para,)))
        assert isinstance(rt.body[0].runs[0], TextRun)
        assert isinstance(rt.body[0].runs[1], Hyperlink)
        assert isinstance(rt.body[0].runs[2], TextRun)


class TestAnchorHyperlinkRoundTrip:
    def _anchor_doc(self, anchor="section1", text="Jump"):
        link = Hyperlink(url=f"#{anchor}", runs=(TextRun(text=text),))
        para = Paragraph(runs=(link,), formatting=ParagraphFormatting())
        return _doc(body=(para,))

    def test_anchor_survives_docx_roundtrip(self):
        rt = _roundtrip_model(self._anchor_doc())
        assert isinstance(rt.body[0].runs[0], Hyperlink)
        assert rt.body[0].runs[0].url == "#section1"

    def test_anchor_survives_html_roundtrip(self):
        rt = _roundtrip_html(self._anchor_doc())
        assert isinstance(rt.body[0].runs[0], Hyperlink)
        assert rt.body[0].runs[0].url == "#section1"

    def test_anchor_not_in_rels(self):
        data = docwow.write_docx(self._anchor_doc())
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "#section1" not in rels_xml
        assert "section1" not in rels_xml

    def test_anchor_html_renders_hash_href(self):
        doc = self._anchor_doc(anchor="intro", text="Go")
        html = docwow.render_document(doc)
        assert 'href="#intro"' in html


class TestHyperlinkDocxRoundTrip:
    def test_hyperlink_survives_docx_roundtrip(self):
        rt = _roundtrip_model(_hyperlink_doc())
        para = rt.body[0]
        assert isinstance(para, Paragraph)
        assert isinstance(para.runs[0], Hyperlink)

    def test_hyperlink_url_preserved(self):
        rt = _roundtrip_model(_hyperlink_doc(url="https://example.com"))
        assert rt.body[0].runs[0].url == "https://example.com"

    def test_hyperlink_text_preserved(self):
        rt = _roundtrip_model(_hyperlink_doc(text="Click here"))
        assert rt.body[0].runs[0].runs[0].text == "Click here"

    def test_mailto_hyperlink_preserved(self):
        rt = _roundtrip_model(_hyperlink_doc(url="mailto:hi@example.com", text="email"))
        assert rt.body[0].runs[0].url == "mailto:hi@example.com"

    def test_docx_rels_contains_hyperlink(self):
        data = docwow.write_docx(_hyperlink_doc())
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "hyperlink" in rels_xml.lower()
        assert "https://example.com" in rels_xml

    def test_docx_rels_targetmode_external(self):
        data = docwow.write_docx(_hyperlink_doc())
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "External" in rels_xml

    def test_multiple_hyperlinks_unique_rids(self):
        link1 = Hyperlink(url="https://a.com", runs=(TextRun(text="A"),))
        link2 = Hyperlink(url="https://b.com", runs=(TextRun(text="B"),))
        para = Paragraph(runs=(link1, link2), formatting=ParagraphFormatting())
        data = docwow.write_docx(_doc(body=(para,)))
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "https://a.com" in rels_xml
        assert "https://b.com" in rels_xml


# ---------------------------------------------------------------------------
# Showcase: regenerated on every test run, used for round-trip checks
# ---------------------------------------------------------------------------

class TestShowcase:
    """
    Regenerates showcase.docx from build_showcase() on every run (so it
    always reflects every feature currently supported), then verifies both
    DOCX and HTML round-trips preserve all key feature types.
    """

    @pytest.fixture(autouse=True, scope="class")
    def showcase_doc(self):
        """Build the showcase Document, write showcase.docx, showcase.html, and showcase_page_view.html."""
        doc = build_showcase()
        data = docwow.write_docx(doc)
        (FIXTURES / "showcase.docx").write_bytes(data)
        html = docwow.render_document(doc)
        (FIXTURES / "showcase.html").write_text(html, encoding="utf-8")
        html_pv = docwow.render_document(doc, page_view=True)
        (FIXTURES / "showcase_page_view.html").write_text(html_pv, encoding="utf-8")
        return doc

    # --- DOCX round-trip ---

    def test_docx_roundtrip_is_valid_zip(self):
        data = (FIXTURES / "showcase.docx").read_bytes()
        assert _is_valid_zip(data)

    def test_docx_roundtrip_has_paragraphs(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        paras = [el for el in doc.body if isinstance(el, Paragraph)]
        assert len(paras) > 5

    def test_docx_roundtrip_has_formatted_runs(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        runs = [
            r for el in doc.body if isinstance(el, Paragraph)
            for r in el.runs if isinstance(r, TextRun)
        ]
        assert any(r.formatting.bold for r in runs)
        assert any(r.formatting.italic for r in runs)
        assert any(r.formatting.color for r in runs)

    def test_docx_roundtrip_has_image(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        images = [
            r for el in doc.body if isinstance(el, Paragraph)
            for r in el.runs if isinstance(r, ImageRun)
        ]
        assert len(images) >= 1
        assert images[0].image.data != b""

    def test_docx_roundtrip_has_list_items(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        list_paras = [
            el for el in doc.body
            if isinstance(el, Paragraph) and el.list_info is not None
        ]
        assert len(list_paras) >= 3

    def test_docx_roundtrip_has_table(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        tables = [el for el in doc.body if isinstance(el, Table)]
        assert len(tables) >= 1

    def test_docx_roundtrip_has_hyperlinks(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        links = [
            r for el in doc.body if isinstance(el, Paragraph)
            for r in el.runs if isinstance(r, Hyperlink)
        ]
        assert len(links) >= 2
        urls = {link.url for link in links}
        assert any("docwow" in u or "github" in u or "mailto" in u for u in urls)

    def test_docx_roundtrip_rels_contains_hyperlinks(self):
        data = (FIXTURES / "showcase.docx").read_bytes()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "hyperlink" in rels_xml.lower()
        assert "External" in rels_xml

    # --- HTML round-trip ---

    def test_html_roundtrip_produces_valid_html(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        assert "<!DOCTYPE html>" in html
        assert "dw-document" in html

    def test_html_roundtrip_preserves_paragraphs(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        rt = docwow.parse_html(html)
        paras = [el for el in rt.body if isinstance(el, Paragraph)]
        assert len(paras) > 5

    def test_html_roundtrip_preserves_hyperlinks(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        rt = docwow.parse_html(html)
        links = [
            r for el in rt.body if isinstance(el, Paragraph)
            for r in el.runs if isinstance(r, Hyperlink)
        ]
        assert len(links) >= 2

    def test_html_roundtrip_preserves_tables(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        rt = docwow.parse_html(html)
        tables = [el for el in rt.body if isinstance(el, Table)]
        assert len(tables) >= 1

    def test_html_roundtrip_preserves_list_items(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        rt = docwow.parse_html(html)
        list_paras = [
            el for el in rt.body
            if isinstance(el, Paragraph) and el.list_info is not None
        ]
        assert len(list_paras) >= 3

    def test_full_pipeline_showcase_docx(self):
        """showcase.docx → HTML → DOCX must produce a valid ZIP."""
        html = docwow.to_html(FIXTURES / "showcase.docx")
        data = docwow.to_docx(html)
        assert _is_valid_zip(data)

    def test_docx_roundtrip_has_header(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        assert doc.header_default is not None
        assert len(doc.header_default.paragraphs) >= 1

    def test_docx_roundtrip_has_footer_with_page_number(self):
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        assert doc.footer_default is not None
        runs = doc.footer_default.paragraphs[0].runs
        assert any(isinstance(r, PageNumberField) for r in runs)

    def test_html_roundtrip_has_header(self):
        # Showcase header has text content — must render as <header> element
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        assert 'dw-header' in html

    def test_html_roundtrip_footer_present_but_hidden(self):
        # Showcase footer is "Page N of M" — page-number-only paragraphs get
        # dw-page-only class (display:none) but the <footer> element IS present
        # so the HTML → DOCX round-trip can recover it
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        assert '<footer' in html
        assert 'dw-page-only' in html

    def test_html_roundtrip_page_break_preserved(self):
        # Page breaks are kept as hidden divs for round-trip fidelity
        doc = docwow.parse_docx(FIXTURES / "showcase.docx")
        html = docwow.render_document(doc)
        assert 'dw-page-break' in html


class TestHeaderFooterDocxRoundTrip:
    """DOCX write → parse round-trip for headers and footers."""

    def _make_doc_with_header(self) -> Document:
        from docwow.models.styles import ParagraphFormatting
        hf = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(TextRun(text="Test Header"),),
                formatting=ParagraphFormatting(),
            ),
        ))
        return Document(
            body=(),
            styles=(),
            numbering=(),
            header_default=hf,
        )

    def _make_doc_with_footer(self) -> Document:
        from docwow.models.styles import ParagraphFormatting
        ftr = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(TextRun(text="Page "), PageNumberField(field_type="PAGE")),
                formatting=ParagraphFormatting(),
            ),
        ))
        return Document(
            body=(),
            styles=(),
            numbering=(),
            footer_default=ftr,
        )

    def test_header_survives_docx_roundtrip(self):
        doc = self._make_doc_with_header()
        data = docwow.write_docx(doc)
        rt = docwow.parse_docx(data)
        assert rt.header_default is not None

    def test_header_text_preserved(self):
        doc = self._make_doc_with_header()
        data = docwow.write_docx(doc)
        rt = docwow.parse_docx(data)
        text = "".join(
            r.text for r in rt.header_default.paragraphs[0].runs
            if isinstance(r, TextRun)
        )
        assert "Test Header" in text

    def test_footer_page_number_preserved(self):
        doc = self._make_doc_with_footer()
        data = docwow.write_docx(doc)
        rt = docwow.parse_docx(data)
        assert rt.footer_default is not None
        runs = rt.footer_default.paragraphs[0].runs
        assert any(isinstance(r, PageNumberField) and r.field_type == "PAGE" for r in runs)

    def test_docx_contains_header_xml(self):
        doc = self._make_doc_with_header()
        data = docwow.write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
        assert any("header" in n for n in names)

    def test_docx_contains_footer_xml(self):
        doc = self._make_doc_with_footer()
        data = docwow.write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
        assert any("footer" in n for n in names)

    def test_docx_content_types_has_header(self):
        doc = self._make_doc_with_header()
        data = docwow.write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            ct_xml = zf.read("[Content_Types].xml").decode("utf-8")
        assert "header+xml" in ct_xml

    def test_docx_document_rels_has_header_rel(self):
        doc = self._make_doc_with_header()
        data = docwow.write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            rels = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "header" in rels.lower()

    def test_no_header_means_no_header_file(self):
        doc = Document(body=(), styles=(), numbering=())
        data = docwow.write_docx(doc)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
        assert not any("header" in n for n in names)

    def test_title_pg_survives_roundtrip(self):
        from docwow.models.styles import ParagraphFormatting
        hf = HeaderFooter(paragraphs=(
            Paragraph(runs=(TextRun(text="First"),), formatting=ParagraphFormatting()),
        ))
        doc = Document(body=(), styles=(), numbering=(), header_first=hf, title_pg=True)
        data = docwow.write_docx(doc)
        rt = docwow.parse_docx(data)
        assert rt.title_pg is True
        assert rt.header_first is not None


class TestHeaderFooterHtmlRoundTrip:
    """HTML render → parse round-trip for headers and footers."""

    def _make_doc(self) -> Document:
        from docwow.models.styles import ParagraphFormatting
        hdr = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(TextRun(text="My Header"),),
                formatting=ParagraphFormatting(),
            ),
        ))
        ftr = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(TextRun(text="Page "), PageNumberField(field_type="PAGE")),
                formatting=ParagraphFormatting(),
            ),
        ))
        return Document(
            body=(),
            styles=(),
            numbering=(),
            header_default=hdr,
            footer_default=ftr,
        )

    def test_html_contains_header_element(self):
        doc = self._make_doc()
        html = docwow.render_document(doc)
        assert 'dw-header' in html

    def test_html_contains_footer_element(self):
        doc = self._make_doc()
        html = docwow.render_document(doc)
        assert 'dw-footer' in html

    def test_html_header_text_present(self):
        doc = self._make_doc()
        html = docwow.render_document(doc)
        assert "My Header" in html

    def test_html_footer_page_field_present_for_roundtrip(self):
        # Page number fields must be present in HTML (as dw-field spans) so
        # that HTML → DOCX round-trip can recover them
        doc = self._make_doc()
        html = docwow.render_document(doc)
        assert 'data-dw-field="PAGE"' in html

    def test_html_footer_page_only_paragraph_is_hidden(self):
        # "Page N" footer is a page-number template — paragraph gets
        # dw-page-only class (display:none) but <footer> element stays in DOM
        doc = self._make_doc()
        html = docwow.render_document(doc)
        assert '<footer' in html
        assert 'dw-page-only' in html

    def test_html_footer_real_content_preserved(self):
        # Footer with non-connector text alongside a page field: text part shown,
        # field stripped — e.g. "Confidential — Page N" → "Confidential — "
        from docwow.models.styles import ParagraphFormatting
        ftr = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(
                    TextRun(text="Confidential — "),
                    PageNumberField(field_type="PAGE"),
                ),
                formatting=ParagraphFormatting(),
            ),
        ))
        doc = Document(body=(), styles=(), numbering=(), footer_default=ftr)
        html = docwow.render_document(doc)
        assert '<footer' in html
        assert 'Confidential' in html

    def test_html_roundtrip_preserves_header(self):
        doc = self._make_doc()
        html = docwow.render_document(doc)
        rt = docwow.parse_html(html)
        assert rt.header_default is not None
        text = "".join(
            r.text for r in rt.header_default.paragraphs[0].runs
            if isinstance(r, TextRun)
        )
        assert "My Header" in text

    def test_html_footer_page_number_only_paragraph_hidden(self):
        # A footer containing ONLY a page number field: <footer> element IS
        # present but the paragraph is hidden (dw-page-only class)
        from docwow.models.styles import ParagraphFormatting
        ftr = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(PageNumberField(field_type="PAGE"),),
                formatting=ParagraphFormatting(),
            ),
        ))
        doc = Document(body=(), styles=(), numbering=(), footer_default=ftr)
        html = docwow.render_document(doc)
        assert '<footer' in html
        assert 'dw-page-only' in html

    def test_html_roundtrip_preserves_footer_page_number_field(self):
        # HTML → parse_html must recover the PageNumberField from a hidden paragraph
        doc = self._make_doc()
        html = docwow.render_document(doc)
        rt = docwow.parse_html(html)
        assert rt.footer_default is not None
        runs = rt.footer_default.paragraphs[0].runs
        assert any(isinstance(r, PageNumberField) for r in runs)


# ---------------------------------------------------------------------------
# DOCX → HTML → DOCX semantic round-trip
# ---------------------------------------------------------------------------

class TestDocxHtmlDocxRoundTrip:
    """Verify that DOCX → render_document() → parse_html() → write_docx() →
    parse_docx() preserves all semantically significant content.

    We don't compare raw XML (attribute order, namespace prefixes, and default
    values differ); instead we assert structural and content equivalence on the
    re-parsed model.
    """

    def _build_doc(self) -> Document:
        """A document with header, page-number footer, body text, and a page break."""
        from docwow.models.styles import ParagraphFormatting
        hdr = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(TextRun(text="Round-trip Header"),),
                formatting=ParagraphFormatting(),
            ),
        ))
        ftr = HeaderFooter(paragraphs=(
            Paragraph(
                runs=(
                    TextRun(text="Page "),
                    PageNumberField(field_type="PAGE"),
                    TextRun(text=" of "),
                    PageNumberField(field_type="NUMPAGES"),
                ),
                formatting=ParagraphFormatting(),
            ),
        ))
        body = (
            Paragraph(runs=(TextRun(text="First page content"),), formatting=ParagraphFormatting()),
            PageBreak(),
            Paragraph(runs=(TextRun(text="Second page content"),), formatting=ParagraphFormatting()),
        )
        return Document(
            body=body,
            styles=(),
            numbering=(),
            header_default=hdr,
            footer_default=ftr,
        )

    def _roundtrip(self, doc: Document) -> Document:
        """DOCX → HTML → DOCX → re-parsed Document."""
        docx_bytes = docwow.write_docx(doc)
        html = docwow.render_document(docwow.parse_docx(docx_bytes))
        rt_docx = docwow.to_docx(html)
        return docwow.parse_docx(rt_docx)

    def test_body_paragraphs_preserved(self):
        rt = self._roundtrip(self._build_doc())
        texts = [
            "".join(r.text for r in el.runs if isinstance(r, TextRun))
            for el in rt.body if isinstance(el, Paragraph)
        ]
        assert "First page content" in texts
        assert "Second page content" in texts

    def test_page_break_preserved(self):
        rt = self._roundtrip(self._build_doc())
        assert any(isinstance(el, PageBreak) for el in rt.body)

    def test_header_text_preserved(self):
        rt = self._roundtrip(self._build_doc())
        assert rt.header_default is not None
        text = "".join(
            r.text for r in rt.header_default.paragraphs[0].runs
            if isinstance(r, TextRun)
        )
        assert "Round-trip Header" in text

    def test_footer_page_number_field_preserved(self):
        rt = self._roundtrip(self._build_doc())
        assert rt.footer_default is not None
        runs = rt.footer_default.paragraphs[0].runs
        page_fields = [r for r in runs if isinstance(r, PageNumberField) and r.field_type == "PAGE"]
        numpages_fields = [r for r in runs if isinstance(r, PageNumberField) and r.field_type == "NUMPAGES"]
        assert len(page_fields) >= 1
        assert len(numpages_fields) >= 1

    def test_footer_connector_text_preserved(self):
        rt = self._roundtrip(self._build_doc())
        assert rt.footer_default is not None
        texts = [
            r.text for r in rt.footer_default.paragraphs[0].runs
            if isinstance(r, TextRun)
        ]
        assert "Page " in texts
        assert " of " in texts

    def test_output_is_valid_docx(self):
        docx_bytes = docwow.write_docx(self._build_doc())
        html = docwow.render_document(docwow.parse_docx(docx_bytes))
        rt_docx = docwow.to_docx(html)
        assert _is_valid_zip(rt_docx)

    def test_showcase_docx_html_docx_header_preserved(self):
        """Full showcase pipeline: showcase.docx → HTML → DOCX → re-parse."""
        docx_bytes = (FIXTURES / "showcase.docx").read_bytes()
        html = docwow.render_document(docwow.parse_docx(docx_bytes))
        rt_docx = docwow.to_docx(html)
        rt = docwow.parse_docx(rt_docx)
        assert rt.header_default is not None
        text = "".join(
            r.text for r in rt.header_default.paragraphs[0].runs
            if isinstance(r, TextRun)
        )
        assert len(text) > 0

    def test_showcase_docx_html_docx_footer_page_field_preserved(self):
        """Showcase footer (page-number-only) survives HTML round-trip."""
        docx_bytes = (FIXTURES / "showcase.docx").read_bytes()
        html = docwow.render_document(docwow.parse_docx(docx_bytes))
        rt_docx = docwow.to_docx(html)
        rt = docwow.parse_docx(rt_docx)
        assert rt.footer_default is not None
        runs = rt.footer_default.paragraphs[0].runs
        assert any(isinstance(r, PageNumberField) for r in runs)

    def test_showcase_docx_html_docx_page_break_preserved(self):
        """Page break in showcase survives HTML round-trip."""
        docx_bytes = (FIXTURES / "showcase.docx").read_bytes()
        html = docwow.render_document(docwow.parse_docx(docx_bytes))
        rt_docx = docwow.to_docx(html)
        rt = docwow.parse_docx(rt_docx)
        assert any(isinstance(el, PageBreak) for el in rt.body)
