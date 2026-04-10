"""
OOXML namespace helpers for docwow.

lxml works with Clark notation for qualified names: {namespace_uri}localname.
Writing these URIs by hand throughout the parser is error-prone and verbose.
This module provides:

  qn("w:p")  →  "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"

and thin wrappers around lxml's find/findall/get that accept the same
"prefix:localname" shorthand.
"""

from __future__ import annotations

from lxml import etree

# ---------------------------------------------------------------------------
# Namespace registry
# ---------------------------------------------------------------------------

NAMESPACES: dict[str, str] = {
    # Core WordprocessingML
    "w":   "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    # Relationships (used inside content parts)
    "r":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    # DrawingML — word-processor drawing anchor/inline
    "wp":  "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    # DrawingML — main drawing primitives
    "a":   "http://schemas.openxmlformats.org/drawingml/2006/main",
    # DrawingML — picture
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    # VML (legacy drawing format still used for some shapes)
    "v":   "urn:schemas-microsoft-com:vml",
    # Markup Compatibility (mc:AlternateContent / mc:Fallback)
    "mc":  "http://schemas.openxmlformats.org/markup-compatibility/2006",
    # Extended WordprocessingML (Word 2010+)
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    # Extended WordprocessingML (Word 2013+)
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    # Content Types
    "ct":  "http://schemas.openxmlformats.org/package/2006/content-types",
    # Package Relationships
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


# ---------------------------------------------------------------------------
# Clark-notation helper
# ---------------------------------------------------------------------------

def qn(tag: str) -> str:
    """Expand a prefixed tag name to lxml Clark notation.

    Examples:
        qn("w:p")   → "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
        qn("r:id")  → "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

    Raises:
        KeyError: if the namespace prefix is not registered in NAMESPACES.
        ValueError: if *tag* does not contain exactly one colon.
    """
    parts = tag.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Tag {tag!r} must be in 'prefix:localname' form (got {len(parts) - 1} colons)"
        )
    prefix, local = parts
    if prefix not in NAMESPACES:
        raise KeyError(
            f"Namespace prefix {prefix!r} is not registered. "
            f"Known prefixes: {sorted(NAMESPACES)}"
        )
    return f"{{{NAMESPACES[prefix]}}}{local}"


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def attrib(
    el: etree._Element,
    attr: str,
    default: str | None = None,
) -> str | None:
    """Return the value of attribute *attr* on *el*, or *default* if absent.

    *attr* may be given in 'prefix:localname' form (expanded via qn) or as
    a plain local name (no namespace).

    Examples:
        attrib(el, "w:val")          # namespaced attribute
        attrib(el, "id")             # plain attribute (no namespace)
        attrib(el, "w:val", "auto")  # with fallback default
    """
    key = qn(attr) if ":" in attr else attr
    return el.get(key, default)


def find(el: etree._Element, path: str) -> etree._Element | None:
    """Find the first child (or descendant) matching *path*.

    *path* may use 'prefix:localname' notation; each component is expanded
    via qn before being passed to lxml.  Simple single-level lookups only
    (e.g. "w:pPr").  For complex XPath, use lxml directly.

    Returns None if not found.
    """
    expanded = "/".join(qn(p) if ":" in p else p for p in path.split("/"))
    return el.find(expanded)


def findall(el: etree._Element, path: str) -> list[etree._Element]:
    """Return all children (or descendants) matching *path*.

    Same path expansion rules as :func:`find`.
    """
    expanded = "/".join(qn(p) if ":" in p else p for p in path.split("/"))
    return el.findall(expanded)


def parse_xml(data: bytes) -> etree._Element:
    """Parse raw XML bytes and return the root element.

    Uses lxml's recovery mode to tolerate minor XML issues in real-world DOCX
    files (e.g. stray control characters, namespace declaration quirks).
    """
    parser = etree.XMLParser(recover=True, remove_comments=True)
    return etree.fromstring(data, parser=parser)
