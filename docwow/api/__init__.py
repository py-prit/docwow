"""
docwow.api — mutable document wrapper layer.

Users interact with these classes directly.  The frozen dataclasses in
docwow.models are an internal implementation detail and should not be
constructed or mutated by user code.
"""

from docwow.api.document import DocumentWrapper
from docwow.api.image import MutableImage
from docwow.api.list_item import MutableListItem
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.run import MutableHyperlink, MutableImageRun, MutableRun, RunCollection
from docwow.api.table import TableCellView, TableRowView, TableView

__all__ = [
    "DocumentWrapper",
    "MutableImage",
    "MutableHyperlink",
    "MutableImageRun",
    "MutableListItem",
    "MutableParagraph",
    "MutableRun",
    "ParagraphCollection",
    "RunCollection",
    "TableCellView",
    "TableRowView",
    "TableView",
]
