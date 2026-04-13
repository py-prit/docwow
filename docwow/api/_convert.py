"""
Conversion helpers between frozen models and mutable wrappers.

These are pure functions with no side effects.  They are the only place
in the codebase where frozen models and mutable wrappers are coupled.
"""

from __future__ import annotations

from docwow.models.document import Document
from docwow.models.footnote import Footnote
from docwow.models.header_footer import HeaderFooter
from docwow.models.paragraph import FootnoteRef, Hyperlink, ImageRun, PageBreak, PageNumberField, Paragraph, Run, TextRun
from docwow.models.table import Table, TableCell, TableRow
from docwow.api.footnote import MutableFootnote, MutableFootnoteRef
from docwow.api.run import MutableHyperlink, MutableImageRun, MutablePageNumberField, MutableRun, RunCollection
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.header_footer import MutableHeaderFooter
from docwow.api.table import MutableTable, MutableTableCell, MutableTableRow


# ---------------------------------------------------------------------------
# Frozen → Wrapper  (used at docwow.open() time)
# ---------------------------------------------------------------------------

def footnote_from_frozen(frozen: Footnote) -> MutableFootnote:
    """Convert a frozen Footnote to a MutableFootnote."""
    collection = ParagraphCollection()
    for para in frozen.paragraphs:
        collection._items.append(paragraph_from_frozen(para))
    return MutableFootnote(
        note_id=frozen.note_id,
        paragraphs=collection,
        note_type=frozen.note_type,
    )


def run_from_frozen(frozen: Run) -> MutableRun | MutableImageRun | MutableHyperlink | MutablePageNumberField | MutableFootnoteRef:
    """Convert a frozen run to its mutable wrapper."""
    if isinstance(frozen, TextRun):
        fmt = frozen.formatting
        return MutableRun(
            text=frozen.text,
            bold=fmt.bold,
            italic=fmt.italic,
            underline=fmt.underline,
            strike=fmt.strike,
            font_name=fmt.font_name,
            font_size=fmt.font_size_pt,
            color=fmt.color,
            highlight=fmt.highlight,
            vertical_align=fmt.vertical_align,
        )
    if isinstance(frozen, ImageRun):
        return MutableImageRun(frozen.image)
    if isinstance(frozen, Hyperlink):
        # Flatten multi-run hyperlink text into a single string
        text = "".join(r.text for r in frozen.runs)
        return MutableHyperlink(text=text, url=frozen.url)
    if isinstance(frozen, PageNumberField):
        return MutablePageNumberField(field_type=frozen.field_type)
    if isinstance(frozen, FootnoteRef):
        return MutableFootnoteRef(note_id=frozen.note_id, note_type=frozen.note_type)
    raise TypeError(f"Unknown run type: {type(frozen).__name__}")


def header_footer_from_frozen(frozen: HeaderFooter) -> MutableHeaderFooter:
    """Convert a frozen HeaderFooter to a MutableHeaderFooter."""
    from docwow.api.paragraph import ParagraphCollection
    collection = ParagraphCollection()
    for para in frozen.paragraphs:
        collection._items.append(paragraph_from_frozen(para))
    return MutableHeaderFooter(paragraphs=collection)


def paragraph_from_frozen(frozen: Paragraph) -> MutableParagraph:
    """Convert a frozen Paragraph to a MutableParagraph (or MutableListItem)."""
    runs = RunCollection()
    for run in frozen.runs:
        runs.append(run_from_frozen(run))

    if frozen.list_info is not None:
        from docwow.api.list_item import MutableListItem
        item = MutableListItem(
            num_id=frozen.list_info.num_id,
            level=frozen.list_info.level,
            formatting=frozen.formatting,
        )
        # Replace the empty RunCollection with the populated one
        item._runs = runs
        return item

    para = MutableParagraph(runs=runs, formatting=frozen.formatting)
    return para


def table_cell_from_frozen(frozen: TableCell) -> MutableTableCell:
    """Convert a frozen TableCell to a MutableTableCell."""
    collection = ParagraphCollection()
    for para in frozen.paragraphs:
        collection._items.append(paragraph_from_frozen(para))
    return MutableTableCell(
        paragraphs=collection,
        col_span=frozen.col_span,
        row_span=frozen.row_span,
        width_pt=frozen.width_pt,
        v_merge_start=frozen.v_merge_start,
        v_merge_continue=frozen.v_merge_continue,
    )


def table_row_from_frozen(frozen: TableRow) -> MutableTableRow:
    """Convert a frozen TableRow to a MutableTableRow."""
    return MutableTableRow(
        cells=[table_cell_from_frozen(c) for c in frozen.cells],
        height_pt=frozen.height_pt,
    )


def table_from_frozen(frozen: Table) -> MutableTable:
    """Convert a frozen Table to a MutableTable."""
    return MutableTable(
        rows=[table_row_from_frozen(r) for r in frozen.rows],
        width_pt=frozen.width_pt,
        style_id=frozen.style_id,
        col_widths_pt=frozen.col_widths_pt,
    )


def document_from_frozen(frozen: Document) -> "DocumentWrapper":
    """Convert a frozen Document to a DocumentWrapper."""
    from docwow.api.document import DocumentWrapper

    collection = ParagraphCollection()
    for element in frozen.body:
        if isinstance(element, Paragraph):
            collection._items.append(paragraph_from_frozen(element))
        elif isinstance(element, Table):
            collection._items.append(table_from_frozen(element))
        elif isinstance(element, PageBreak):
            collection._items.append(element)  # already frozen, pass through

    def _hf(hf: HeaderFooter | None) -> MutableHeaderFooter | None:
        return header_footer_from_frozen(hf) if hf is not None else None

    return DocumentWrapper(
        paragraphs=collection,
        styles=frozen.styles,
        numbering=frozen.numbering,
        page_width_pt=frozen.page_width_pt,
        page_height_pt=frozen.page_height_pt,
        margin_top_pt=frozen.margin_top_pt,
        margin_bottom_pt=frozen.margin_bottom_pt,
        margin_left_pt=frozen.margin_left_pt,
        margin_right_pt=frozen.margin_right_pt,
        header_default=_hf(frozen.header_default),
        header_first=_hf(frozen.header_first),
        header_even=_hf(frozen.header_even),
        footer_default=_hf(frozen.footer_default),
        footer_first=_hf(frozen.footer_first),
        footer_even=_hf(frozen.footer_even),
        title_pg=frozen.title_pg,
        footnotes=[footnote_from_frozen(n) for n in frozen.footnotes],
        endnotes=[footnote_from_frozen(n) for n in frozen.endnotes],
    )


# ---------------------------------------------------------------------------
# Wrapper → Frozen  (used at save() / to_bytes() time)
# ---------------------------------------------------------------------------

def document_to_frozen(wrapper: "DocumentWrapper") -> Document:
    """Convert a DocumentWrapper to a frozen Document for pipeline use."""
    def _hf_frozen(hf: MutableHeaderFooter | None) -> HeaderFooter | None:
        return hf._to_frozen() if hf is not None else None

    return Document(
        body=wrapper.paragraphs._to_frozen_body(),
        styles=wrapper._styles,
        numbering=wrapper._numbering,
        page_width_pt=wrapper.page_width_pt,
        page_height_pt=wrapper.page_height_pt,
        margin_top_pt=wrapper.margin_top_pt,
        margin_bottom_pt=wrapper.margin_bottom_pt,
        margin_left_pt=wrapper.margin_left_pt,
        margin_right_pt=wrapper.margin_right_pt,
        header_default=_hf_frozen(wrapper._header_default),
        header_first=_hf_frozen(wrapper._header_first),
        header_even=_hf_frozen(wrapper._header_even),
        footer_default=_hf_frozen(wrapper._footer_default),
        footer_first=_hf_frozen(wrapper._footer_first),
        footer_even=_hf_frozen(wrapper._footer_even),
        title_pg=wrapper._title_pg,
        footnotes=wrapper._footnotes_frozen,
        endnotes=wrapper._endnotes_frozen,
    )
