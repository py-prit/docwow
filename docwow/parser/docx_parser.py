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

from docwow.models.comment import Comment
from docwow.models.document import Document
from docwow.models.footnote import Footnote
from docwow.models.header_footer import HeaderFooter
from docwow.models.section import SectionProperties
from docwow.parser.body_parser import parse_body
from docwow.parser.comment_parser import parse_comments
from docwow.parser.footnote_parser import parse_footnotes
from docwow.parser.header_footer_parser import parse_header_footer
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

    # -----------------------------------------------------------------------
    # Headers and footers
    # -----------------------------------------------------------------------
    hf = _parse_headers_footers(doc_root, zf, relationships, names)

    # -----------------------------------------------------------------------
    # Footnotes and endnotes
    # -----------------------------------------------------------------------
    footnotes: tuple[Footnote, ...] = ()
    if "word/footnotes.xml" in names:
        footnotes = parse_footnotes(
            zf.read("word/footnotes.xml"), zf, relationships, note_type="footnote"
        )

    endnotes: tuple[Footnote, ...] = ()
    if "word/endnotes.xml" in names:
        endnotes = parse_footnotes(
            zf.read("word/endnotes.xml"), zf, relationships, note_type="endnote"
        )

    comments: tuple[Comment, ...] = ()
    if "word/comments.xml" in names:
        comments = parse_comments(zf.read("word/comments.xml"), zf, relationships)

    return Document(
        body=body,
        styles=styles,
        numbering=numbering,
        page_width_pt=page_width_pt,
        page_height_pt=page_height_pt,
        footnotes=footnotes,
        endnotes=endnotes,
        comments=comments,
        **margins,
        **hf,
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


def parse_sect_pr(sect_pr, break_type: str = "nextPage") -> SectionProperties:
    """Parse a w:sectPr element into a SectionProperties object."""
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

    type_el = find(sect_pr, "w:type")
    if type_el is not None:
        raw = attrib(type_el, "w:val")
        if raw:
            break_type = raw

    return SectionProperties(
        page_width_pt=page_width_pt,
        page_height_pt=page_height_pt,
        margin_top_pt=margin_top_pt,
        margin_bottom_pt=margin_bottom_pt,
        margin_left_pt=margin_left_pt,
        margin_right_pt=margin_right_pt,
        break_type=break_type,
    )


def _parse_page_geometry(doc_root: object) -> tuple[float, float, dict]:
    """Extract page size and margins from w:sectPr."""
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

    props = parse_sect_pr(sect_pr)
    return props.page_width_pt, props.page_height_pt, {
        "margin_top_pt": props.margin_top_pt,
        "margin_bottom_pt": props.margin_bottom_pt,
        "margin_left_pt": props.margin_left_pt,
        "margin_right_pt": props.margin_right_pt,
    }


# ---------------------------------------------------------------------------
# Headers and footers
# ---------------------------------------------------------------------------

_REL_HEADER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
_REL_FOOTER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"


def _parse_headers_footers(
    doc_root,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    names: list[str],
) -> dict:
    """Parse header/footer references from sectPr and return a dict of kwargs."""
    result: dict = {}

    body_el = find(doc_root, "w:body")
    sect_pr = None
    if body_el is not None:
        sect_pr = find(body_el, "w:sectPr")
    if sect_pr is None:
        sect_pr = find(doc_root, "w:sectPr")
    if sect_pr is None:
        return result

    # Detect different first page
    title_pg_el = find(sect_pr, "w:titlePg")
    if title_pg_el is not None:
        val = attrib(title_pg_el, "w:val")
        result["title_pg"] = val != "0"

    # Collect rId→target map limited to header/footer types
    # relationships already contains ALL rels; we need the file targets
    # But parse_relationships returns {rId: target_value}.
    # For headers/footers the target is a file path like "header1.xml".
    # We need to also know the *type* (header vs footer) per rId.
    # Re-read the rels XML to get type info.
    rels_path = "word/_rels/document.xml.rels"
    hf_rels: dict[str, tuple[str, str]] = {}  # rId → (type, target)
    if rels_path in names:
        rels_root = parse_xml(zf.read(rels_path))
        PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
        for rel in rels_root:
            rel_type = rel.get("Type", "")
            if rel_type in (_REL_HEADER, _REL_FOOTER):
                rid = rel.get("Id", "")
                target = rel.get("Target", "")
                hf_rels[rid] = (rel_type, target)

    # Map sectPr headerReference/footerReference to parsed HeaderFooter objects
    _hdr_type_map = {
        "default": "header_default",
        "first":   "header_first",
        "even":    "header_even",
    }
    _ftr_type_map = {
        "default": "footer_default",
        "first":   "footer_first",
        "even":    "footer_even",
    }

    for ref_tag, type_map, rel_type_uri in (
        ("w:headerReference", _hdr_type_map, _REL_HEADER),
        ("w:footerReference", _ftr_type_map, _REL_FOOTER),
    ):
        for ref_el in sect_pr.findall(qn(ref_tag)):
            hf_type = attrib(ref_el, "w:type") or "default"
            rid = attrib(ref_el, "r:id") or ""
            if rid not in hf_rels:
                continue
            rel_type, target = hf_rels[rid]
            if rel_type != rel_type_uri:
                continue
            # target is relative to "word/" e.g. "header1.xml"
            part_path = f"word/{target}"
            if part_path not in names:
                continue
            hf_obj = parse_header_footer(zf.read(part_path), zf, relationships)
            field_name = type_map.get(hf_type)
            if field_name:
                result[field_name] = hf_obj

    return result
