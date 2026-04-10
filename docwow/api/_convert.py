"""
Conversion helpers between frozen models and mutable wrappers.

These are pure functions with no side effects.  They are the only place
in the codebase where frozen models and mutable wrappers are coupled.
"""

from __future__ import annotations

from docwow.models.document import Document
from docwow.models.paragraph import ImageRun, Paragraph, Run, TextRun
from docwow.models.table import Table
from docwow.api.run import MutableImageRun, MutableRun, RunCollection
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.table import TableView


# ---------------------------------------------------------------------------
# Frozen → Wrapper  (used at docwow.open() time)
# ---------------------------------------------------------------------------

def run_from_frozen(frozen: Run) -> MutableRun | MutableImageRun:
    """Convert a frozen TextRun or ImageRun to its mutable wrapper."""
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
    raise TypeError(f"Unknown run type: {type(frozen).__name__}")


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


def document_from_frozen(frozen: Document) -> "DocumentWrapper":
    """Convert a frozen Document to a DocumentWrapper."""
    from docwow.api.document import DocumentWrapper

    collection = ParagraphCollection()
    for element in frozen.body:
        if isinstance(element, Paragraph):
            collection._items.append(paragraph_from_frozen(element))
        elif isinstance(element, Table):
            collection._items.append(TableView(element))

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
    )


# ---------------------------------------------------------------------------
# Wrapper → Frozen  (used at save() / to_bytes() time)
# ---------------------------------------------------------------------------

def document_to_frozen(wrapper: "DocumentWrapper") -> Document:
    """Convert a DocumentWrapper to a frozen Document for pipeline use."""
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
    )
