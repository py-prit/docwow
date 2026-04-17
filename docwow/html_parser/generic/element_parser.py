"""DOM walker: HTML elements → Document model.

Built incrementally across Phase 2 sub-features:
  feat/generic-block-elements   — h1-h6, p, div, blockquote, pre, hr, br
  feat/generic-inline-elements  — b/i/u/s/code/mark/sub/sup/span/a + CSS
  feat/generic-lists             — ul/ol/li
  feat/generic-tables            — table/tr/td/th
  feat/generic-images            — img
"""
from __future__ import annotations

from docwow.models.document import Document
from docwow.models.paragraph import Paragraph
from docwow.models.styles import ParagraphFormatting


class ElementParser:
    """Walks the HTML DOM and builds a :class:`~docwow.models.document.Document`."""

    def __init__(self, fetch_images: bool = False, fetch_external_css: bool = False) -> None:
        self.fetch_images = fetch_images
        self.fetch_external_css = fetch_external_css

    def parse(self, html: str) -> Document:
        """Parse an HTML string and return a Document.  Stub — filled in by sub-features."""
        # Placeholder: returns an empty document until block element support lands.
        return Document(body=(), styles=(), numbering=())
