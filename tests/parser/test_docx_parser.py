"""Tests for docwow.parser.docx_parser — top-level parse_docx()."""
from pathlib import Path

import pytest

from docwow.models.document import Document
from docwow.models.paragraph import Paragraph
from docwow.models.table import Table
from docwow.parser.docx_parser import parse_docx

FIXTURES = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Accepts both path and bytes
# ---------------------------------------------------------------------------

class TestParseDocxInputForms:
    def test_accepts_path_object(self):
        doc = parse_docx(FIXTURES / "empty.docx")
        assert isinstance(doc, Document)

    def test_accepts_string_path(self):
        doc = parse_docx(str(FIXTURES / "empty.docx"))
        assert isinstance(doc, Document)

    def test_accepts_bytes(self, empty_docx):
        doc = parse_docx(empty_docx)
        assert isinstance(doc, Document)

    def test_returns_document_instance(self, empty_docx):
        assert isinstance(parse_docx(empty_docx), Document)


# ---------------------------------------------------------------------------
# Empty document
# ---------------------------------------------------------------------------

class TestEmptyDocument:
    def test_body_is_empty(self, empty_docx):
        doc = parse_docx(empty_docx)
        assert doc.body == ()

    def test_has_styles(self, empty_docx):
        # Even an empty doc has default styles
        doc = parse_docx(empty_docx)
        assert len(doc.styles) > 0

    def test_page_geometry_is_populated(self, empty_docx):
        doc = parse_docx(empty_docx)
        assert doc.page_width_pt > 0
        assert doc.page_height_pt > 0
        assert doc.margin_top_pt > 0


# ---------------------------------------------------------------------------
# Page geometry (python-docx uses US Letter by default: 12240 × 15840 twips)
# ---------------------------------------------------------------------------

class TestPageGeometry:
    def test_page_width_reasonable(self, paragraphs_docx):
        doc = parse_docx(paragraphs_docx)
        # Any standard page: wider than 400pt, narrower than 900pt
        assert 400 < doc.page_width_pt < 900

    def test_page_height_reasonable(self, paragraphs_docx):
        doc = parse_docx(paragraphs_docx)
        assert 500 < doc.page_height_pt < 1300

    def test_margins_are_positive(self, paragraphs_docx):
        doc = parse_docx(paragraphs_docx)
        assert doc.margin_top_pt > 0
        assert doc.margin_bottom_pt > 0
        assert doc.margin_left_pt > 0
        assert doc.margin_right_pt > 0

    def test_us_letter_width(self, paragraphs_docx):
        # python-docx default template is Letter: 12240 twips = 612 pt
        doc = parse_docx(paragraphs_docx)
        assert doc.page_width_pt == pytest.approx(612.0, abs=1.0)


# ---------------------------------------------------------------------------
# Paragraphs document
# ---------------------------------------------------------------------------

class TestParagraphsDocument:
    def test_body_contains_paragraphs(self, paragraphs_docx):
        doc = parse_docx(paragraphs_docx)
        assert len(doc.body) > 0
        assert all(isinstance(el, Paragraph) for el in doc.body)

    def test_heading_styles_present(self, paragraphs_docx):
        doc = parse_docx(paragraphs_docx)
        style_ids = {
            p.formatting.style_id
            for p in doc.body
            if isinstance(p, Paragraph)
        }
        # Headings 1–3 should appear
        assert any("Heading" in (s or "") or "heading" in (s or "") for s in style_ids)

    def test_paragraph_text_extracted(self, paragraphs_docx):
        doc = parse_docx(paragraphs_docx)
        all_text = " ".join(
            run.text
            for p in doc.body
            if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text")
        )
        assert "Heading 1" in all_text
        assert "Normal paragraph" in all_text

    def test_alignment_parsed(self, paragraphs_docx):
        doc = parse_docx(paragraphs_docx)
        alignments = {
            p.formatting.alignment
            for p in doc.body
            if isinstance(p, Paragraph)
        }
        assert "center" in alignments or "right" in alignments or "justify" in alignments


# ---------------------------------------------------------------------------
# Formatting document
# ---------------------------------------------------------------------------

class TestFormattingDocument:
    def test_bold_run_present(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        bold_runs = [
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.bold
        ]
        assert len(bold_runs) > 0

    def test_italic_run_present(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        italic_runs = [
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.italic
        ]
        assert len(italic_runs) > 0

    def test_underline_run_present(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        ul_runs = [
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.underline
        ]
        assert len(ul_runs) > 0

    def test_strike_run_present(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        st_runs = [
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.strike
        ]
        assert len(st_runs) > 0

    def test_font_size_parsed(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        sizes = [
            run.formatting.font_size_pt
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.font_size_pt is not None
        ]
        assert len(sizes) > 0
        assert 8.0 in sizes or any(s == pytest.approx(8.0) for s in sizes)
        assert any(s == pytest.approx(24.0) for s in sizes)

    def test_color_parsed(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        colors = [
            run.formatting.color
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.color is not None
        ]
        assert len(colors) > 0
        assert "FF0000" in colors

    def test_font_name_parsed(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        fonts = [
            run.formatting.font_name
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.font_name is not None
        ]
        assert "Arial" in fonts

    def test_superscript_parsed(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        va_values = [
            run.formatting.vertical_align
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.vertical_align is not None
        ]
        assert "superscript" in va_values

    def test_subscript_parsed(self, formatting_docx):
        doc = parse_docx(formatting_docx)
        va_values = [
            run.formatting.vertical_align
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text") and run.formatting.vertical_align is not None
        ]
        assert "subscript" in va_values


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class TestTableSimple:
    def test_table_present_in_body(self, table_simple_docx):
        doc = parse_docx(table_simple_docx)
        tables = [el for el in doc.body if isinstance(el, Table)]
        assert len(tables) == 1

    def test_table_has_three_rows(self, table_simple_docx):
        doc = parse_docx(table_simple_docx)
        table = next(el for el in doc.body if isinstance(el, Table))
        assert len(table.rows) == 3

    def test_table_rows_have_three_cells(self, table_simple_docx):
        doc = parse_docx(table_simple_docx)
        table = next(el for el in doc.body if isinstance(el, Table))
        for row in table.rows:
            assert len(row.cells) == 3

    def test_cell_text_extracted(self, table_simple_docx):
        doc = parse_docx(table_simple_docx)
        table = next(el for el in doc.body if isinstance(el, Table))
        first_cell_text = "".join(
            run.text
            for p in table.rows[0].cells[0].paragraphs
            for run in p.runs
            if hasattr(run, "text")
        )
        assert "R1C1" in first_cell_text

    def test_surrounding_paragraphs_parsed(self, table_simple_docx):
        doc = parse_docx(table_simple_docx)
        paragraphs = [el for el in doc.body if isinstance(el, Paragraph)]
        assert len(paragraphs) >= 2  # "Before" and "After" paragraphs

    def test_col_widths_parsed(self, table_simple_docx):
        doc = parse_docx(table_simple_docx)
        table = next(el for el in doc.body if isinstance(el, Table))
        assert len(table.col_widths_pt) == 3
        assert all(w > 0 for w in table.col_widths_pt)


class TestTableMerged:
    def test_horizontal_merge_detected(self, table_merged_docx):
        doc = parse_docx(table_merged_docx)
        table = next(el for el in doc.body if isinstance(el, Table))
        first_row = table.rows[0]
        merged_cell = first_row.cells[0]
        assert merged_cell.col_span == 2

    def test_vertical_merge_start_detected(self, table_merged_docx):
        doc = parse_docx(table_merged_docx)
        table = next(el for el in doc.body if isinstance(el, Table))
        # The cell at row 0, col 2 should start a vertical merge
        first_row_last_cell = table.rows[0].cells[-1]
        assert first_row_last_cell.v_merge_start is True

    def test_vertical_merge_continue_detected(self, table_merged_docx):
        doc = parse_docx(table_merged_docx)
        table = next(el for el in doc.body if isinstance(el, Table))
        # Row 1 last cell is a continuation
        second_row_last_cell = table.rows[1].cells[-1]
        assert second_row_last_cell.v_merge_continue is True


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------

class TestListBullet:
    def test_list_info_present(self, list_bullet_docx):
        doc = parse_docx(list_bullet_docx)
        list_paras = [
            p for p in doc.body
            if isinstance(p, Paragraph) and p.list_info is not None
        ]
        assert len(list_paras) == 5

    def test_list_level_is_zero(self, list_bullet_docx):
        doc = parse_docx(list_bullet_docx)
        for p in doc.body:
            if isinstance(p, Paragraph) and p.list_info is not None:
                assert p.list_info.level == 0

    def test_numbering_definitions_populated(self, list_bullet_docx):
        doc = parse_docx(list_bullet_docx)
        assert len(doc.numbering) > 0


class TestListNumbered:
    def test_list_info_present(self, list_numbered_docx):
        doc = parse_docx(list_numbered_docx)
        list_paras = [
            p for p in doc.body
            if isinstance(p, Paragraph) and p.list_info is not None
        ]
        assert len(list_paras) == 5

    def test_numbering_definitions_populated(self, list_numbered_docx):
        doc = parse_docx(list_numbered_docx)
        assert len(doc.numbering) > 0


class TestListNested:
    # python-docx generates nested visual indentation by assigning a separate
    # numId per list style (ListBullet → numId=1, ListBullet2 → numId=2, …)
    # with each always at ilvl=0.  Real Word documents may instead use one
    # numId with different ilvl values — both patterns are valid OOXML.
    # These tests verify what the fixture actually contains.

    def test_list_paragraphs_present(self, list_nested_docx):
        doc = parse_docx(list_nested_docx)
        list_paras = [
            p for p in doc.body
            if isinstance(p, Paragraph) and p.list_info is not None
        ]
        assert len(list_paras) > 0

    def test_multiple_distinct_num_ids(self, list_nested_docx):
        # Each visual indent level uses its own numId in this fixture
        doc = parse_docx(list_nested_docx)
        num_ids = {
            p.list_info.num_id
            for p in doc.body
            if isinstance(p, Paragraph) and p.list_info is not None
        }
        assert len(num_ids) > 1

    def test_all_list_paragraphs_have_list_info(self, list_nested_docx):
        doc = parse_docx(list_nested_docx)
        list_paras = [
            p for p in doc.body
            if isinstance(p, Paragraph) and p.list_info is not None
        ]
        assert all(p.list_info.num_id != "0" for p in list_paras)


# ---------------------------------------------------------------------------
# Inline image
# ---------------------------------------------------------------------------

class TestInlineImage:
    def test_image_run_present(self, image_inline_docx):
        from docwow.models.paragraph import ImageRun
        doc = parse_docx(image_inline_docx)
        image_runs = [
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if isinstance(run, ImageRun)
        ]
        assert len(image_runs) == 1

    def test_image_has_bytes(self, image_inline_docx):
        from docwow.models.paragraph import ImageRun
        doc = parse_docx(image_inline_docx)
        image_run = next(
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if isinstance(run, ImageRun)
        )
        assert len(image_run.image.data) > 0

    def test_image_dimensions_in_pt(self, image_inline_docx):
        from docwow.models.paragraph import ImageRun
        doc = parse_docx(image_inline_docx)
        image_run = next(
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if isinstance(run, ImageRun)
        )
        assert image_run.image.width_pt > 0
        assert image_run.image.height_pt > 0

    def test_image_content_type_is_png(self, image_inline_docx):
        from docwow.models.paragraph import ImageRun
        doc = parse_docx(image_inline_docx)
        image_run = next(
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if isinstance(run, ImageRun)
        )
        assert image_run.image.content_type == "image/png"

    def test_surrounding_paragraphs_intact(self, image_inline_docx):
        doc = parse_docx(image_inline_docx)
        all_text = " ".join(
            run.text
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if hasattr(run, "text")
        )
        assert "before" in all_text.lower()
        assert "after" in all_text.lower()


# ---------------------------------------------------------------------------
# Mixed document
# ---------------------------------------------------------------------------

class TestMixedDocument:
    def test_has_paragraphs_and_tables(self, mixed_docx):
        doc = parse_docx(mixed_docx)
        has_para = any(isinstance(el, Paragraph) for el in doc.body)
        has_table = any(isinstance(el, Table) for el in doc.body)
        assert has_para
        assert has_table

    def test_has_list_paragraphs(self, mixed_docx):
        doc = parse_docx(mixed_docx)
        list_paras = [
            p for p in doc.body
            if isinstance(p, Paragraph) and p.list_info is not None
        ]
        assert len(list_paras) > 0

    def test_has_image(self, mixed_docx):
        from docwow.models.paragraph import ImageRun
        doc = parse_docx(mixed_docx)
        image_runs = [
            run
            for p in doc.body if isinstance(p, Paragraph)
            for run in p.runs
            if isinstance(run, ImageRun)
        ]
        assert len(image_runs) > 0

    def test_styles_populated(self, mixed_docx):
        doc = parse_docx(mixed_docx)
        assert len(doc.styles) > 0

    def test_numbering_populated(self, mixed_docx):
        doc = parse_docx(mixed_docx)
        assert len(doc.numbering) > 0
