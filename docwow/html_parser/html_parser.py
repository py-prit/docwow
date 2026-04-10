"""
Parse docwow-generated HTML back into a Document model.

The HTML produced by render_document() encodes all Word metadata in
data-dw-* attributes, so the round-trip is lossless for structure and
formatting.  Styles are reconstructed as minimal Style objects (style_id
and name only); full style declarations are preserved per-paragraph via
the data attributes on each <p> element.
"""
from __future__ import annotations

import lxml.html

from docwow.html_parser._utils import has_class, pt_val
from docwow.html_parser.paragraph_parser import parse_paragraph
from docwow.html_parser.table_parser import parse_table
from docwow.models.document import Document
from docwow.models.lists import ListLevel, NumberingDefinition
from docwow.models.paragraph import Paragraph
from docwow.models.styles import Style
from docwow.models.table import Table


def parse_html(source: str | bytes) -> Document:
    """Parse a docwow HTML string back into a Document model.

    Args:
        source: HTML produced by ``render_document()``, as a string or
                UTF-8 bytes.

    Returns:
        A :class:`~docwow.models.document.Document` whose body, geometry,
        styles, and numbering reflect the content of the HTML.

    Raises:
        ValueError: If the HTML does not contain a ``dw-document`` element.
    """
    if isinstance(source, str):
        source = source.encode("utf-8")
    root = lxml.html.document_fromstring(source)

    divs = root.xpath('.//div[contains(@class,"dw-document")]')
    if not divs:
        raise ValueError("HTML does not contain a dw-document element")
    doc_div = divs[0]

    # Page geometry — fall back to A4 / 1-inch margins if attributes absent
    g = doc_div.get
    page_width_pt    = pt_val(g("data-dw-page-width"),    595.28)
    page_height_pt   = pt_val(g("data-dw-page-height"),   841.89)
    margin_top_pt    = pt_val(g("data-dw-margin-top"),    72.0)
    margin_bottom_pt = pt_val(g("data-dw-margin-bottom"), 72.0)
    margin_left_pt   = pt_val(g("data-dw-margin-left"),   72.0)
    margin_right_pt  = pt_val(g("data-dw-margin-right"),  72.0)

    body, numbering, style_ids = _parse_body(doc_div)

    # Minimal Style objects: carry the style_id so the writer can reference them
    styles = tuple(
        Style(style_id=sid, name=sid, style_type="paragraph")
        for sid in sorted(style_ids)
    )

    return Document(
        body=body,
        styles=styles,
        numbering=numbering,
        page_width_pt=page_width_pt,
        page_height_pt=page_height_pt,
        margin_top_pt=margin_top_pt,
        margin_bottom_pt=margin_bottom_pt,
        margin_left_pt=margin_left_pt,
        margin_right_pt=margin_right_pt,
    )


# ---------------------------------------------------------------------------
# Body traversal
# ---------------------------------------------------------------------------

def _parse_body(
    doc_div,
) -> tuple[tuple[Paragraph | Table, ...], tuple[NumberingDefinition, ...], set[str]]:
    """Walk direct children of the dw-document div and build the body tuple."""
    body: list[Paragraph | Table] = []
    style_ids: set[str] = set()
    # num_id → {level → num_fmt}
    numbering_levels: dict[str, dict[int, str]] = {}

    for child in doc_div:
        tag = child.tag
        if tag == "p" and has_class(child, "dw-p"):
            para = parse_paragraph(child)
            body.append(para)
            _collect_style(para, style_ids)

        elif tag == "table" and has_class(child, "dw-table"):
            body.append(parse_table(child))

        elif tag in ("ul", "ol") and has_class(child, "dw-list"):
            _collect_list(child, body, style_ids, numbering_levels)

    return tuple(body), _build_numbering(numbering_levels), style_ids


def _collect_list(
    list_el,
    body: list,
    style_ids: set[str],
    numbering_levels: dict[str, dict[int, str]],
) -> None:
    """Extract paragraphs from a dw-list element, handling nesting."""
    num_id = list_el.get("data-dw-num-id", "")
    num_fmt = "bullet" if list_el.tag == "ul" else "decimal"

    for li in list_el:
        if li.tag != "li":
            continue
        level = int(li.get("data-dw-level", "0"))
        numbering_levels.setdefault(num_id, {})[level] = num_fmt

        for child in li:
            if child.tag == "p" and has_class(child, "dw-p"):
                para = parse_paragraph(child)
                body.append(para)
                _collect_style(para, style_ids)
            elif child.tag in ("ul", "ol") and has_class(child, "dw-list"):
                _collect_list(child, body, style_ids, numbering_levels)


def _collect_style(para: Paragraph, style_ids: set[str]) -> None:
    if para.formatting.style_id:
        style_ids.add(para.formatting.style_id)


def _build_numbering(
    numbering_levels: dict[str, dict[int, str]],
) -> tuple[NumberingDefinition, ...]:
    return tuple(
        NumberingDefinition(
            abstract_num_id=num_id,
            levels=tuple(
                ListLevel(level=lvl, num_fmt=fmt)
                for lvl, fmt in sorted(levels.items())
            ),
        )
        for num_id, levels in sorted(numbering_levels.items())
    )
