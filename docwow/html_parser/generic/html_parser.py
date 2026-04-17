"""Entry point for generic HTML → DOCX conversion.

This module is built incrementally across Phase 2 sub-features.
Each sub-feature adds support for more HTML elements and CSS properties.
"""
from __future__ import annotations

from docwow.models.document import Document
from docwow.models.styles import ParagraphFormatting


def parse_foreign_html(
    html: str | bytes,
    fetch_images: bool = False,
    fetch_external_css: bool = False,
) -> Document:
    """Parse arbitrary HTML into a :class:`~docwow.models.document.Document`.

    This is a best-effort conversion.  HTML constructs with no Word equivalent
    are skipped with a :class:`~docwow.DocwowConversionWarning`.

    Args:
        html:               HTML string or UTF-8 bytes from any source.
        fetch_images:       Download remote ``<img src="https://...">`` URLs.
        fetch_external_css: Download ``<link rel="stylesheet">`` URLs.

    Returns:
        A :class:`~docwow.models.document.Document` ready for the DOCX writer.
    """
    from docwow.html_parser.generic.element_parser import ElementParser

    if isinstance(html, bytes):
        html = html.decode("utf-8")

    parser = ElementParser(
        fetch_images=fetch_images,
        fetch_external_css=fetch_external_css,
    )
    return parser.parse(html)
