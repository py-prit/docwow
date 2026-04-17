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
import re

from docwow.models.document import Document
from docwow.models.header_footer import HeaderFooter
from docwow.models.paragraph import PageBreak, PageNumberField, Paragraph, TextRun
from docwow.models.table import Table
from docwow.models.toc import TableOfContents
from docwow.renderer.css_generator import generate_css
from docwow.renderer.comment_renderer import render_comments
from docwow.renderer.footnote_renderer import render_endnotes, render_footnotes
from docwow.renderer.list_renderer import render_list_group
from docwow.renderer.paragraph_renderer import render_paragraph
from docwow.renderer.table_renderer import render_table
from docwow.renderer.toc_renderer import render_toc
from docwow.utils.units import pt_to_css


def render_document(
    doc: Document,
    embed_images: bool = True,
    page_view: bool = False,
) -> str:
    """Render a Document to a complete, self-contained HTML string.

    Args:
        doc:           The document model to render.
        embed_images:  When True (default), images are embedded as base64
                       data URIs.  When False, a placeholder src is used
                       (useful for testing without large base64 blobs).
        page_view:     When True, adds CSS that styles the document as a
                       physical page (gray background, drop shadow) and
                       injects an ``@media print`` block with ``@page``
                       size/margin rules so the browser paginates correctly
                       when printing or exporting to PDF.

    Returns:
        A UTF-8 HTML string starting with <!DOCTYPE html>.
    """
    css = generate_css(doc, page_view=page_view)
    header_html = _render_hf_slots(doc, kind="header")
    footer_html = _render_hf_slots(doc, kind="footer")
    body_html = _render_body(doc, page_view=page_view)
    footnotes_html = render_footnotes(doc.footnotes)
    endnotes_html = render_endnotes(doc.endnotes)
    comments_html = render_comments(doc.comments)
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
        f"{header_html}"
        f'<div {doc_attrs}>\n'
        f"{body_html}\n"
        "</div>\n"
        f"{footnotes_html}"
        f"{endnotes_html}"
        f"{comments_html}"
        f"{footer_html}"
        f"<script>\n{_TRACK_CHANGES_JS}\n</script>\n"
        "</body>\n"
        "</html>"
    )


def _render_hf_slots(doc: Document, kind: str) -> str:
    """Render all header or footer slots of the given kind."""
    slots = {
        "header": [
            (doc.header_default, "default"),
            (doc.header_first,   "first"),
            (doc.header_even,    "even"),
        ],
        "footer": [
            (doc.footer_default, "default"),
            (doc.footer_first,   "first"),
            (doc.footer_even,    "even"),
        ],
    }[kind]
    parts: list[str] = []
    for hf, hf_type in slots:
        if hf is not None:
            parts.append(_render_hf_element(hf, kind, hf_type))
    return "".join(parts)


# Words that are only meaningful as connectors around a page-number field.
# A paragraph consisting entirely of these + PageNumberFields is hidden.
_PAGE_CONNECTOR_RE = re.compile(
    r'^(?:page|pg|p\.?|of|[-–—/|.,;:·\s]|\d+)*$',
    re.IGNORECASE,
)


def _is_page_number_paragraph(para: Paragraph) -> bool:
    """Return True if the paragraph is a page-number template with no other content.

    Examples that return True:  "Page N of M",  "N / M",  "Page N"
    Examples that return False: "Company — Page N",  "My Header"
    """
    if not any(isinstance(r, PageNumberField) for r in para.runs):
        return False
    for run in para.runs:
        if isinstance(run, PageNumberField):
            continue
        if isinstance(run, TextRun) and _PAGE_CONNECTOR_RE.match(run.text):
            continue
        return False  # contains non-connector content
    return True


def _render_hf_element(hf: HeaderFooter, element: str, hf_type: str) -> str:
    """Render a header/footer element.

    All paragraphs are rendered so that the HTML → DOCX round-trip is lossless.
    Paragraphs that are purely page-number templates ("Page N of M") are given
    the ``dw-page-only`` CSS class (``display:none``) so they are invisible in
    the browser but their ``data-dw-field`` spans survive for round-trip.
    Paragraphs with real text content are rendered normally; any PageNumberField
    runs appear as gray italic placeholder spans (e.g. "Company — 1").
    If the element has no paragraphs at all it is omitted.
    """
    if not hf.paragraphs:
        return ""

    lines: list[str] = []
    for para in hf.paragraphs:
        if _is_page_number_paragraph(para):
            # Hidden visually but present in DOM for round-trip fidelity
            lines.append(render_paragraph(para, extra_classes=["dw-page-only"]))
        else:
            lines.append(render_paragraph(para))

    css_class = f"dw-{element} dw-{element}-{hf_type}"
    data_attr = f'data-dw-{element}-type="{hf_type}"'
    inner = "\n".join(lines)
    return f'<{element} class="{css_class}" {data_attr}>\n{inner}\n</{element}>\n'


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
    if doc.title_pg:
        data["data-dw-title-pg"] = "true"
    data_str = " ".join(f'{k}="{v}"' for k, v in data.items())
    return f'class="dw-document" {data_str}'


def _render_body(doc: Document, page_view: bool = False) -> str:
    """Render all body elements, grouping list paragraphs."""
    comments_lookup = {c.comment_id: c for c in doc.comments}
    parts: list[str] = []
    list_buffer: list[Paragraph] = []
    page_num = [1]  # mutable counter

    def flush_list() -> None:
        if list_buffer:
            parts.append(render_list_group(list_buffer, doc.numbering, comments=comments_lookup))
            list_buffer.clear()

    for element in doc.body:
        if isinstance(element, Paragraph):
            if element.list_info is not None:
                list_buffer.append(element)
            else:
                flush_list()
                parts.append(render_paragraph(element, comments=comments_lookup))
        elif isinstance(element, Table):
            flush_list()
            parts.append(render_table(element))
        elif isinstance(element, TableOfContents):
            flush_list()
            parts.append(render_toc(element))
        elif isinstance(element, PageBreak):
            flush_list()
            page_num[0] += 1
            parts.append(_render_page_break(page_num[0], page_view))

    flush_list()
    return "\n".join(parts)


def _render_page_break(page_num: int, page_view: bool) -> str:
    # Always hidden in HTML — preserved only for round-trip DOCX fidelity.
    # Visual page-view rendering is a planned future feature.
    return f'<div class="dw-page-break" data-dw-page="{page_num}"></div>'


# ---------------------------------------------------------------------------
# Track-changes accept / reject JavaScript
# ---------------------------------------------------------------------------

_TRACK_CHANGES_JS = """\
function dwTcAccept(btn) {
  var el = btn.closest('ins.dw-ins, del.dw-del');
  if (!el) return;
  if (el.tagName === 'INS') {
    _dwTcUnwrap(el);   // accept insert  → keep text, remove markup
  } else {
    el.parentNode.removeChild(el);  // accept delete → remove text
  }
}
function dwTcReject(btn) {
  var el = btn.closest('ins.dw-ins, del.dw-del');
  if (!el) return;
  if (el.tagName === 'DEL') {
    _dwTcUnwrap(el);   // reject delete  → keep text, remove markup
  } else {
    el.parentNode.removeChild(el);  // reject insert → remove text
  }
}
function _dwTcUnwrap(el) {
  var parent = el.parentNode;
  Array.from(el.childNodes).forEach(function(child) {
    if (!(child.classList && child.classList.contains('dw-tc-popup'))) {
      parent.insertBefore(child, el);
    }
  });
  parent.removeChild(el);
}"""
