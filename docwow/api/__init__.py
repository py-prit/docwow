"""
docwow.api — mutable document wrapper layer.

Users interact with these classes directly.  The frozen dataclasses in
docwow.models are an internal implementation detail and should not be
constructed or mutated by user code.
"""

from docwow.api.document import DocumentWrapper
from docwow.api.footnote import MutableFootnote, MutableFootnoteRef
from docwow.api.header_footer import MutableHeaderFooter
from docwow.api.image import MutableImage
from docwow.api.list_item import MutableListItem
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.run import MutableBookmark, MutableHyperlink, MutableImageRun, MutablePageNumberField, MutableRun, RunCollection
from docwow.api.table import (
    MutableTable,
    MutableTableCell,
    MutableTableRow,
    # Backward-compatibility aliases
    TableView,
    TableRowView,
    TableCellView,
)
from docwow.api.toc import MutableTableOfContents, MutableTocEntry

__all__ = [
    "DocumentWrapper",
    "MutableBookmark",
    "MutableFootnote",
    "MutableFootnoteRef",
    "MutableHeaderFooter",
    "MutableImage",
    "MutableHyperlink",
    "MutableImageRun",
    "MutableListItem",
    "MutablePageNumberField",
    "MutableParagraph",
    "MutableRun",
    "MutableTable",
    "MutableTableCell",
    "MutableTableOfContents",
    "MutableTableRow",
    "MutableTocEntry",
    "ParagraphCollection",
    "RunCollection",
    # Backward-compatibility aliases
    "TableCellView",
    "TableRowView",
    "TableView",
]
