"""Build the structural/static XML parts of a DOCX archive.

These are the small parts that don't depend on document content:
  - [Content_Types].xml
  - _rels/.rels
  - word/_rels/document.xml.rels
  - word/settings.xml
"""
from __future__ import annotations

from lxml import etree

from docwow.writer._xml import (
    CT_NS, PKG_NS, W,
    REL_DOCUMENT, REL_STYLES, REL_NUMBERING, REL_SETTINGS, REL_IMAGE,
    to_bytes,
)


# ---------------------------------------------------------------------------
# [Content_Types].xml
# ---------------------------------------------------------------------------

def build_content_types_xml(
    image_entries: list[tuple[str, str]],
    has_numbering: bool,
) -> bytes:
    """Build ``[Content_Types].xml``.

    Args:
        image_entries: ``[(part_name, content_type), ...]`` e.g.
                       ``[("/word/media/image1.png", "image/png")]``
        has_numbering: True when the document contains list paragraphs.
    """
    root = etree.Element(f"{{{CT_NS}}}Types", nsmap={None: CT_NS})

    def _default(ext: str, ct: str) -> None:
        el = etree.SubElement(root, f"{{{CT_NS}}}Default")
        el.set("Extension", ext)
        el.set("ContentType", ct)

    def _override(part: str, ct: str) -> None:
        el = etree.SubElement(root, f"{{{CT_NS}}}Override")
        el.set("PartName", part)
        el.set("ContentType", ct)

    _default("rels", "application/vnd.openxmlformats-package.relationships+xml")
    _default("xml", "application/xml")
    _override(
        "/word/document.xml",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    )
    _override(
        "/word/styles.xml",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
    )
    _override(
        "/word/settings.xml",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml",
    )
    if has_numbering:
        _override(
            "/word/numbering.xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml",
        )
    for part_name, ct in image_entries:
        _override(part_name, ct)

    return to_bytes(root)


# ---------------------------------------------------------------------------
# _rels/.rels
# ---------------------------------------------------------------------------

def build_root_rels_xml() -> bytes:
    """Build the package root ``_rels/.rels`` pointing at word/document.xml."""
    root = etree.Element(f"{{{PKG_NS}}}Relationships", nsmap={None: PKG_NS})
    el = etree.SubElement(root, f"{{{PKG_NS}}}Relationship")
    el.set("Id", "rId1")
    el.set("Type", REL_DOCUMENT)
    el.set("Target", "word/document.xml")
    return to_bytes(root)


# ---------------------------------------------------------------------------
# word/_rels/document.xml.rels
# ---------------------------------------------------------------------------

def build_document_rels_xml(
    rel_entries: list[tuple],
) -> bytes:
    """Build ``word/_rels/document.xml.rels``.

    Args:
        rel_entries: ``[(rid, type_uri, target), ...]`` or
                     ``[(rid, type_uri, target, target_mode), ...]``.
                     ``target_mode`` is written as ``TargetMode`` when present
                     (e.g. ``"External"`` for hyperlinks).
    """
    root = etree.Element(f"{{{PKG_NS}}}Relationships", nsmap={None: PKG_NS})
    for entry in rel_entries:
        rid, type_uri, target = entry[0], entry[1], entry[2]
        target_mode = entry[3] if len(entry) > 3 else None
        el = etree.SubElement(root, f"{{{PKG_NS}}}Relationship")
        el.set("Id", rid)
        el.set("Type", type_uri)
        el.set("Target", target)
        if target_mode:
            el.set("TargetMode", target_mode)
    return to_bytes(root)


# ---------------------------------------------------------------------------
# word/settings.xml
# ---------------------------------------------------------------------------

def build_settings_xml() -> bytes:
    """Build a minimal ``word/settings.xml``."""
    root = etree.Element(f"{{{W}}}settings", nsmap={"w": W})
    tab = etree.SubElement(root, f"{{{W}}}defaultTabStop")
    tab.set(f"{{{W}}}val", "720")
    etree.SubElement(root, f"{{{W}}}compat")
    return to_bytes(root)
