"""
Extract inline image data from the DOCX zip.

A DOCX file is a zip archive.  Images are stored under word/media/.
Each image is referenced from word/document.xml via a relationship ID (rId),
which is resolved through word/_rels/document.xml.rels.

This module provides:
  - parse_relationships()  — rId → target path mapping
  - extract_image()        — rId → InlineImage (bytes + dimensions)
"""

from __future__ import annotations

import zipfile
from lxml import etree

from docwow.models.image import InlineImage
from docwow.utils.units import emu_to_pt
from docwow.utils.xml_utils import attrib, findall, qn, NAMESPACES

# MIME type by file extension
_CONTENT_TYPES: dict[str, str] = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".bmp":  "image/bmp",
    ".tiff": "image/tiff",
    ".tif":  "image/tiff",
    ".webp": "image/webp",
    ".emf":  "image/x-emf",
    ".wmf":  "image/x-wmf",
}


def parse_relationships(rels_xml: bytes) -> dict[str, str]:
    """Parse word/_rels/document.xml.rels → {rId: target_path}.

    Target paths are stored relative to the word/ directory, so a target of
    "media/image1.png" resolves to "word/media/image1.png" in the zip.
    """
    root = etree.fromstring(rels_xml)
    result: dict[str, str] = {}
    for rel in root:
        rid = rel.get("Id")
        target = rel.get("Target")
        if rid and target:
            # Normalise to the zip path (strip leading "/" if present)
            result[rid] = target.lstrip("/")
    return result


def extract_image(
    zf: zipfile.ZipFile,
    relationship_id: str,
    relationships: dict[str, str],
    cx_emu: int,
    cy_emu: int,
    alt_text: str = "",
) -> InlineImage | None:
    """Build an InlineImage from a zip file and relationship metadata.

    Args:
        zf:               Open DOCX zip archive.
        relationship_id:  The rId from the drawing XML (e.g. "rId5").
        relationships:    Mapping from parse_relationships().
        cx_emu:           Image width in EMU (from wp:extent/@cx).
        cy_emu:           Image height in EMU (from wp:extent/@cy).
        alt_text:         Accessibility description (may be empty).

    Returns:
        InlineImage, or None if the relationship target can't be found in
        the zip (e.g. linked rather than embedded image).
    """
    target = relationships.get(relationship_id)
    if target is None:
        return None

    # Relationship targets are relative to word/, so prepend if needed
    zip_path = target if target.startswith("word/") else f"word/{target}"

    try:
        data = zf.read(zip_path)
    except KeyError:
        # File not present in zip (e.g. external/linked image)
        return None

    suffix = "." + zip_path.rsplit(".", 1)[-1].lower() if "." in zip_path else ""
    content_type = _CONTENT_TYPES.get(suffix, "application/octet-stream")

    return InlineImage(
        relationship_id=relationship_id,
        content_type=content_type,
        data=data,
        width_pt=emu_to_pt(cx_emu),
        height_pt=emu_to_pt(cy_emu),
        alt_text=alt_text,
    )
