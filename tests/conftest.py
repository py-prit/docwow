"""Shared fixtures for the docwow test suite."""

import pytest

from docwow.models import (
    Document,
    ImageRun,
    InlineImage,
    ListInfo,
    ListLevel,
    NumberingDefinition,
    Paragraph,
    ParagraphFormatting,
    RunFormatting,
    Style,
    Table,
    TableCell,
    TableRow,
    TextRun,
)

# ---------------------------------------------------------------------------
# Formatting primitives
# ---------------------------------------------------------------------------

@pytest.fixture
def default_run_fmt() -> RunFormatting:
    return RunFormatting()


@pytest.fixture
def bold_run_fmt() -> RunFormatting:
    return RunFormatting(bold=True, font_size_pt=12.0, color="000000")


@pytest.fixture
def default_para_fmt() -> ParagraphFormatting:
    return ParagraphFormatting()


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

PNG_HEADER = b"\x89PNG\r\n\x1a\n"   # first 8 bytes of any PNG file


@pytest.fixture
def sample_image() -> InlineImage:
    return InlineImage(
        relationship_id="rId1",
        content_type="image/png",
        data=PNG_HEADER,
        width_pt=100.0,
        height_pt=50.0,
    )


# ---------------------------------------------------------------------------
# Runs & Paragraphs
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_text_run() -> TextRun:
    return TextRun(text="Hello, World!")


@pytest.fixture
def sample_image_run(sample_image) -> ImageRun:
    return ImageRun(image=sample_image)


@pytest.fixture
def sample_paragraph(sample_text_run) -> Paragraph:
    return Paragraph(runs=(sample_text_run,))


@pytest.fixture
def sample_list_info() -> ListInfo:
    return ListInfo(num_id="1", level=0)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_cell(sample_paragraph) -> TableCell:
    return TableCell(paragraphs=(sample_paragraph,))


@pytest.fixture
def sample_row(sample_cell) -> TableRow:
    return TableRow(cells=(sample_cell,))


@pytest.fixture
def sample_table(sample_row) -> Table:
    return Table(rows=(sample_row,))


# ---------------------------------------------------------------------------
# Styles & Numbering
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_style() -> Style:
    return Style(style_id="Heading1", name="heading 1", style_type="paragraph")


@pytest.fixture
def sample_list_level() -> ListLevel:
    return ListLevel(level=0, num_fmt="decimal")


@pytest.fixture
def sample_numbering(sample_list_level) -> NumberingDefinition:
    return NumberingDefinition(abstract_num_id="0", levels=(sample_list_level,))


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_document(sample_paragraph) -> Document:
    return Document(body=(sample_paragraph,), styles=(), numbering=())
