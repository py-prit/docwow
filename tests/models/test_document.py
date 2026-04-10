"""Tests for docwow.models.document — Document, BodyElement."""

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.document import BodyElement, Document
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.models.table import Table, TableCell, TableRow

# A4 dimensions in points (default)
A4_WIDTH_PT = 595.28
A4_HEIGHT_PT = 841.89
ONE_INCH_PT = 72.0


# ---------------------------------------------------------------------------
# Default page geometry
# ---------------------------------------------------------------------------

class TestDocumentDefaults:
    def test_page_width_a4(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.page_width_pt == pytest.approx(A4_WIDTH_PT)

    def test_page_height_a4(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.page_height_pt == pytest.approx(A4_HEIGHT_PT)

    def test_margin_top_one_inch(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.margin_top_pt == pytest.approx(ONE_INCH_PT)

    def test_margin_bottom_one_inch(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.margin_bottom_pt == pytest.approx(ONE_INCH_PT)

    def test_margin_left_one_inch(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.margin_left_pt == pytest.approx(ONE_INCH_PT)

    def test_margin_right_one_inch(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.margin_right_pt == pytest.approx(ONE_INCH_PT)


# ---------------------------------------------------------------------------
# Custom page geometry
# ---------------------------------------------------------------------------

class TestDocumentCustomPageSize:
    def test_us_letter_width(self):
        # Letter: 8.5 × 11 inches = 612 × 792 pt
        doc = Document(body=(), styles=(), numbering=(), page_width_pt=612.0, page_height_pt=792.0)
        assert doc.page_width_pt == pytest.approx(612.0)
        assert doc.page_height_pt == pytest.approx(792.0)

    def test_landscape_orientation(self):
        # Landscape A4: swap width and height
        doc = Document(body=(), styles=(), numbering=(), page_width_pt=A4_HEIGHT_PT, page_height_pt=A4_WIDTH_PT)
        assert doc.page_width_pt > doc.page_height_pt

    def test_custom_margins(self):
        doc = Document(
            body=(), styles=(), numbering=(),
            margin_top_pt=36.0,
            margin_bottom_pt=36.0,
            margin_left_pt=54.0,
            margin_right_pt=54.0,
        )
        assert doc.margin_top_pt == pytest.approx(36.0)
        assert doc.margin_bottom_pt == pytest.approx(36.0)
        assert doc.margin_left_pt == pytest.approx(54.0)
        assert doc.margin_right_pt == pytest.approx(54.0)

    def test_asymmetric_margins(self):
        # Mirror margins (book layout)
        doc = Document(body=(), styles=(), numbering=(), margin_left_pt=90.0, margin_right_pt=54.0)
        assert doc.margin_left_pt != doc.margin_right_pt


# ---------------------------------------------------------------------------
# Body content
# ---------------------------------------------------------------------------

class TestDocumentBody:
    def test_empty_body(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.body == ()

    def test_single_paragraph(self, sample_paragraph):
        doc = Document(body=(sample_paragraph,), styles=(), numbering=())
        assert len(doc.body) == 1
        assert doc.body[0] == sample_paragraph

    def test_single_table(self, sample_table):
        doc = Document(body=(sample_table,), styles=(), numbering=())
        assert len(doc.body) == 1
        assert isinstance(doc.body[0], Table)

    def test_mixed_body(self, sample_paragraph, sample_table):
        doc = Document(body=(sample_paragraph, sample_table, sample_paragraph), styles=(), numbering=())
        assert len(doc.body) == 3
        assert isinstance(doc.body[0], Paragraph)
        assert isinstance(doc.body[1], Table)
        assert isinstance(doc.body[2], Paragraph)

    def test_multiple_paragraphs(self):
        ps = tuple(
            Paragraph(runs=(TextRun(text=f"Para {i}"),))
            for i in range(10)
        )
        doc = Document(body=ps, styles=(), numbering=())
        assert len(doc.body) == 10
        assert doc.body[9].runs[0].text == "Para 9"

    def test_list_paragraph_in_body(self):
        from docwow.models.lists import ListInfo
        li = ListInfo(num_id="1", level=0)
        p = Paragraph(runs=(TextRun(text="Item"),), list_info=li)
        doc = Document(body=(p,), styles=(), numbering=())
        assert doc.body[0].list_info is not None


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

class TestDocumentStyles:
    def test_empty_styles(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.styles == ()

    def test_single_style(self, sample_style):
        doc = Document(body=(), styles=(sample_style,), numbering=())
        assert len(doc.styles) == 1
        assert doc.styles[0] == sample_style

    def test_multiple_styles(self):
        styles = tuple(
            Style(style_id=f"Style{i}", name=f"Style {i}", style_type="paragraph")
            for i in range(5)
        )
        doc = Document(body=(), styles=styles, numbering=())
        assert len(doc.styles) == 5


# ---------------------------------------------------------------------------
# Numbering
# ---------------------------------------------------------------------------

class TestDocumentNumbering:
    def test_empty_numbering(self):
        doc = Document(body=(), styles=(), numbering=())
        assert doc.numbering == ()

    def test_single_numbering_definition(self, sample_numbering):
        doc = Document(body=(), styles=(), numbering=(sample_numbering,))
        assert len(doc.numbering) == 1
        assert doc.numbering[0] == sample_numbering

    def test_multiple_numbering_definitions(self):
        level = ListLevel(level=0, num_fmt="decimal")
        defs = tuple(
            NumberingDefinition(abstract_num_id=str(i), levels=(level,))
            for i in range(3)
        )
        doc = Document(body=(), styles=(), numbering=defs)
        assert len(doc.numbering) == 3


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

class TestDocumentImmutability:
    def test_cannot_set_body(self, sample_document):
        with pytest.raises(FrozenInstanceError):
            sample_document.body = ()  # type: ignore[misc]

    def test_cannot_set_styles(self, sample_document):
        with pytest.raises(FrozenInstanceError):
            sample_document.styles = ()  # type: ignore[misc]

    def test_cannot_set_numbering(self, sample_document):
        with pytest.raises(FrozenInstanceError):
            sample_document.numbering = ()  # type: ignore[misc]

    def test_cannot_set_page_width(self, sample_document):
        with pytest.raises(FrozenInstanceError):
            sample_document.page_width_pt = 612.0  # type: ignore[misc]

    def test_cannot_set_margin_top(self, sample_document):
        with pytest.raises(FrozenInstanceError):
            sample_document.margin_top_pt = 36.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

class TestDocumentRequiredFields:
    def test_missing_body_raises(self):
        with pytest.raises(TypeError):
            Document(styles=(), numbering=())  # type: ignore[call-arg]

    def test_missing_styles_raises(self):
        with pytest.raises(TypeError):
            Document(body=(), numbering=())  # type: ignore[call-arg]

    def test_missing_numbering_raises(self):
        with pytest.raises(TypeError):
            Document(body=(), styles=())  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Equality & hashing
# ---------------------------------------------------------------------------

class TestDocumentEquality:
    def test_equal_empty(self):
        d1 = Document(body=(), styles=(), numbering=())
        d2 = Document(body=(), styles=(), numbering=())
        assert d1 == d2

    def test_not_equal_different_page_width(self):
        d1 = Document(body=(), styles=(), numbering=(), page_width_pt=595.28)
        d2 = Document(body=(), styles=(), numbering=(), page_width_pt=612.0)
        assert d1 != d2

    def test_not_equal_different_body(self, sample_paragraph):
        d1 = Document(body=(), styles=(), numbering=())
        d2 = Document(body=(sample_paragraph,), styles=(), numbering=())
        assert d1 != d2


class TestDocumentHashable:
    def test_can_be_used_in_set(self):
        d = Document(body=(), styles=(), numbering=())
        s = {d, d}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# BodyElement type alias
# ---------------------------------------------------------------------------

class TestBodyElementTypeAlias:
    def test_paragraph_is_body_element(self, sample_paragraph):
        assert isinstance(sample_paragraph, (Paragraph, Table))

    def test_table_is_body_element(self, sample_table):
        assert isinstance(sample_table, (Paragraph, Table))
