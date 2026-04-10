"""
Top-level DOCX parser.

A DOCX file is a ZIP archive containing XML parts.  This module opens the
archive, reads the relevant parts, delegates to the specialist parsers, and
assembles the final Document object.

Zip layout (parts we care about for v0.1):
    [Content_Types].xml
    word/document.xml          — body content
    word/styles.xml            — named styles
    word/numbering.xml         — list definitions  (optional)
    word/theme/theme1.xml      — theme colours     (optional)
    word/_rels/document.xml.rels — relationships (rId → file path)
    word/media/*               — embedded images
    word/settings.xml          — document settings (page size via sectPr)
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from docwow.models.document import Document
from docwow.parser.body_parser import parse_body
from docwow.parser.image_parser import parse_relationships
from docwow.parser.numbering_parser import parse_numbering
from docwow.parser.style_parser import parse_style_numbering, parse_styles
from docwow.utils.units import twips_to_pt
from docwow.utils.xml_utils import attrib, find, parse_xml, qn


def parse_docx(source: str | Path | bytes) -> Document:
    """Parse a DOCX file and return a Document.

    Args:
        source: Path to a .docx file (str or Path), or raw bytes of the
                zip archive (useful in tests and web upload handlers).

    Returns:
        A fully populated Document ready for rendering.
    """
    if isinstance(source, (str, Path)):
        with open(source, "rb") as fh:
            data = fh.read()
    else:
        data = source

    import io
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return _parse_zip(zf)


def _parse_zip(zf: zipfile.ZipFile) -> Document:
    names = zf.namelist()

    # -----------------------------------------------------------------------
    # Styles
    # -----------------------------------------------------------------------
    styles = ()
    style_num_map: dict[str, tuple[str, int]] = {}
    if "word/styles.xml" in names:
        styles_xml = zf.read("word/styles.xml")
        styles = parse_styles(styles_xml)
        style_num_map = parse_style_numbering(styles_xml)

    # -----------------------------------------------------------------------
    # Numbering
    # -----------------------------------------------------------------------
    numbering = ()
    if "word/numbering.xml" in names:
        numbering = parse_numbering(zf.read("word/numbering.xml"))

    # -----------------------------------------------------------------------
    # Relationships  (rId → media path)
    # -----------------------------------------------------------------------
    relationships: dict[str, str] = {}
    rels_path = "word/_rels/document.xml.rels"
    if rels_path in names:
        relationships = parse_relationships(zf.read(rels_path))

    # -----------------------------------------------------------------------
    # Body
    # -----------------------------------------------------------------------
    doc_xml = zf.read("word/document.xml")
    doc_root = parse_xml(doc_xml)
    body_el = find(doc_root, "w:body")
    if body_el is None:
        body = ()
    else:
        body = parse_body(body_el, zf, relationships, style_num_map)

    # -----------------------------------------------------------------------
    # Page geometry from w:sectPr  (in body or in document root)
    # -----------------------------------------------------------------------
    page_width_pt, page_height_pt, margins = _parse_page_geometry(doc_root)

    return Document(
        body=body,
        styles=styles,
        numbering=numbering,
        page_width_pt=page_width_pt,
        page_height_pt=page_height_pt,
        **margins,
    )


# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------

_A4_W = 595.28
_A4_H = 841.89
_ONE_INCH = 72.0

_DEFAULTS = dict(
    page_width_pt=_A4_W,
    page_height_pt=_A4_H,
    margin_top_pt=_ONE_INCH,
    margin_bottom_pt=_ONE_INCH,
    margin_left_pt=_ONE_INCH,
    margin_right_pt=_ONE_INCH,
)


def _parse_page_geometry(doc_root: object) -> tuple[float, float, dict]:
    """Extract page size and margins from w:sectPr."""
    # sectPr lives either directly in w:body or as a child of w:body
    body_el = find(doc_root, "w:body")
    sect_pr = None
    if body_el is not None:
        sect_pr = find(body_el, "w:sectPr")
    if sect_pr is None:
        sect_pr = find(doc_root, "w:sectPr")

    if sect_pr is None:
        return _A4_W, _A4_H, {
            "margin_top_pt": _ONE_INCH,
            "margin_bottom_pt": _ONE_INCH,
            "margin_left_pt": _ONE_INCH,
            "margin_right_pt": _ONE_INCH,
        }

    page_width_pt = _A4_W
    page_height_pt = _A4_H
    pgSz = find(sect_pr, "w:pgSz")
    if pgSz is not None:
        w_val = attrib(pgSz, "w:w")
        h_val = attrib(pgSz, "w:h")
        if w_val is not None:
            page_width_pt = twips_to_pt(int(w_val))
        if h_val is not None:
            page_height_pt = twips_to_pt(int(h_val))

    margin_top_pt = _ONE_INCH
    margin_bottom_pt = _ONE_INCH
    margin_left_pt = _ONE_INCH
    margin_right_pt = _ONE_INCH
    pgMar = find(sect_pr, "w:pgMar")
    if pgMar is not None:
        top = attrib(pgMar, "w:top")
        bottom = attrib(pgMar, "w:bottom")
        left = attrib(pgMar, "w:left")
        right = attrib(pgMar, "w:right")
        if top is not None:
            margin_top_pt = twips_to_pt(int(top))
        if bottom is not None:
            margin_bottom_pt = twips_to_pt(int(bottom))
        if left is not None:
            margin_left_pt = twips_to_pt(int(left))
        if right is not None:
            margin_right_pt = twips_to_pt(int(right))

    return page_width_pt, page_height_pt, {
        "margin_top_pt": margin_top_pt,
        "margin_bottom_pt": margin_bottom_pt,
        "margin_left_pt": margin_left_pt,
        "margin_right_pt": margin_right_pt,
    }
