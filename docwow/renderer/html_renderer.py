"""
Top-level HTML renderer.

Assembles a complete HTML document from a Document model by:
  1. Generating a CSS <style> block via css_generator
  2. Iterating over body elements
  3. Grouping consecutive list paragraphs and delegating to list_renderer
  4. Delegating non-list paragraphs to paragraph_renderer
  5. Delegating tables to table_renderer
"""

from __future__ import annotations

import html as html_mod

from docwow.models.document import Document
from docwow.models.paragraph import Paragraph
from docwow.models.table import Table
from docwow.renderer.css_generator import generate_css
from docwow.renderer.list_renderer import render_list_group
from docwow.renderer.paragraph_renderer import render_paragraph
from docwow.renderer.table_renderer import render_table
from docwow.utils.units import pt_to_css


def render_document(doc: Document, embed_images: bool = True) -> str:
    """Render a Document to a complete, self-contained HTML string.

    Args:
        doc:           The document model to render.
        embed_images:  When True (default), images are embedded as base64
                       data URIs.  When False, a placeholder src is used
                       (useful for testing without large base64 blobs).

    Returns:
        A UTF-8 HTML string starting with <!DOCTYPE html>.
    """
    css = generate_css(doc)
    body_html = _render_body(doc)
    doc_attrs = _document_attrs(doc)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"<style>\n{css}\n</style>\n"
        "</head>\n"
        "<body>\n"
        f'<div {doc_attrs}>\n'
        f"{body_html}\n"
        "</div>\n"
        "</body>\n"
        "</html>"
    )


def _document_attrs(doc: Document) -> str:
    """Build the attribute string for the root <div class="dw-document">."""
    data = {
        "data-dw-page-width":    pt_to_css(doc.page_width_pt),
        "data-dw-page-height":   pt_to_css(doc.page_height_pt),
        "data-dw-margin-top":    pt_to_css(doc.margin_top_pt),
        "data-dw-margin-bottom": pt_to_css(doc.margin_bottom_pt),
        "data-dw-margin-left":   pt_to_css(doc.margin_left_pt),
        "data-dw-margin-right":  pt_to_css(doc.margin_right_pt),
    }
    data_str = " ".join(f'{k}="{v}"' for k, v in data.items())
    return f'class="dw-document" {data_str}'


def _render_body(doc: Document) -> str:
    """Render all body elements, grouping list paragraphs."""
    parts: list[str] = []
    list_buffer: list[Paragraph] = []

    def flush_list() -> None:
        if list_buffer:
            parts.append(render_list_group(list_buffer, doc.numbering))
            list_buffer.clear()

    for element in doc.body:
        if isinstance(element, Paragraph):
            if element.list_info is not None:
                list_buffer.append(element)
            else:
                flush_list()
                parts.append(render_paragraph(element))
        elif isinstance(element, Table):
            flush_list()
            parts.append(render_table(element))

    flush_list()
    return "\n".join(parts)
