"""Shared XML construction utilities for the docwow DOCX writer.

All OOXML parts are built with lxml.etree.  This module defines namespace
constants and thin helpers so the builder modules stay readable.
"""
from __future__ import annotations

from lxml import etree

# ---------------------------------------------------------------------------
# Namespace URIs
# ---------------------------------------------------------------------------

W   = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP  = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A   = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
XML = "http://www.w3.org/XML/1998/namespace"

# Package namespaces
CT_NS  = "http://schemas.openxmlformats.org/package/2006/content-types"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

# Relationship type URIs
REL_DOCUMENT  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
REL_STYLES    = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
REL_NUMBERING = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering"
REL_SETTINGS  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"
REL_IMAGE      = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
REL_HYPERLINK  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
REL_HEADER     = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
REL_FOOTER     = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
REL_FOOTNOTES  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
REL_ENDNOTES   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/endnotes"
REL_COMMENTS   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"

# Namespace maps for each XML part
DOC_NSMAP = {"w": W, "r": R, "wp": WP, "a": A, "pic": PIC}
STYLE_NSMAP = {"w": W, "r": R}
NUM_NSMAP = {"w": W}

# XML namespace attribute (xml:space="preserve")
XML_SPACE = f"{{{XML}}}space"


# ---------------------------------------------------------------------------
# Element helpers
# ---------------------------------------------------------------------------

def wn(local: str) -> str:
    """Clark-notation tag in the w: namespace."""
    return f"{{{W}}}{local}"


def rn(local: str) -> str:
    """Clark-notation attr in the r: namespace."""
    return f"{{{R}}}{local}"


def sub(parent: etree._Element, local: str, **w_attrs: str) -> etree._Element:
    """Append a w:-namespaced child with optional w:-namespaced attrs."""
    el = etree.SubElement(parent, wn(local))
    for k, v in w_attrs.items():
        el.set(wn(k), v)
    return el


def to_bytes(root: etree._Element) -> bytes:
    """Serialise an element tree to UTF-8 XML bytes with XML declaration."""
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )


# ---------------------------------------------------------------------------
# Unit conversion (pt → OOXML units)
# ---------------------------------------------------------------------------

def pt_tw(pt: float) -> str:
    """Points to twips (1 pt = 20 twips)."""
    return str(int(round(pt * 20)))


def pt_emu(pt: float) -> str:
    """Points to EMU (1 pt = 12700 EMU)."""
    return str(int(round(pt * 12700)))


def pt_hp(pt: float) -> str:
    """Points to half-points (1 pt = 2 half-pts) for w:sz."""
    return str(int(round(pt * 2)))
