"""
Top-level DOCX writer.

Assembles all XML parts into a valid ZIP-based DOCX file:
  [Content_Types].xml
  _rels/.rels
  word/document.xml
  word/_rels/document.xml.rels
  word/styles.xml
  word/numbering.xml  (only when the document has list paragraphs)
  word/settings.xml
  word/media/*        (one file per unique embedded image)
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from docwow.models.document import Document
from docwow.models.image import InlineImage
from docwow.models.paragraph import Hyperlink, ImageRun, Paragraph
from docwow.models.table import Table
from docwow.writer._xml import (
    REL_HYPERLINK, REL_IMAGE, REL_STYLES, REL_NUMBERING, REL_SETTINGS,
)
from docwow.writer.document_writer import build_document_xml
from docwow.writer.numbering_writer import build_numbering_xml
from docwow.writer.parts_writer import (
    build_content_types_xml,
    build_document_rels_xml,
    build_root_rels_xml,
    build_settings_xml,
)
from docwow.writer.styles_writer import build_styles_xml

# content_type → file extension
_EXTENSIONS: dict[str, str] = {
    "image/png":     ".png",
    "image/jpeg":    ".jpg",
    "image/jpg":     ".jpg",
    "image/gif":     ".gif",
    "image/bmp":     ".bmp",
    "image/tiff":    ".tiff",
    "image/webp":    ".webp",
    "image/svg+xml": ".svg",
    "image/x-emf":   ".emf",
    "image/x-wmf":   ".wmf",
}


def write_docx(doc: Document, target: str | Path | None = None) -> bytes:
    """Write a Document to a DOCX byte string.

    Args:
        doc:    The document model to serialise.
        target: Optional file path.  When provided the bytes are also written
                to disk.

    Returns:
        The raw DOCX bytes (a valid ZIP archive).
    """
    data = _build_zip(doc)
    if target is not None:
        Path(target).write_bytes(data)
    return data


# ---------------------------------------------------------------------------
# ZIP assembly
# ---------------------------------------------------------------------------

def _build_zip(doc: Document) -> bytes:
    # 1. Collect unique images in document order
    images = _collect_images(doc)

    # 2. Assign each unique image a media path and a relationship ID
    #    image_info: {original_rid → (new_rid, media_filename, content_type, data)}
    image_info: dict[str, tuple[str, str, str, bytes]] = {}
    counter = 1
    for img in images:
        if img.relationship_id not in image_info:
            ext = _EXTENSIONS.get(img.content_type, ".bin")
            filename = f"image{counter}{ext}"
            new_rid = f"rId{counter}"
            image_info[img.relationship_id] = (new_rid, filename, img.content_type, img.data)
            counter += 1

    # Relationship ID budget after images
    next_rid = counter   # next available integer

    has_numbering = bool(doc.numbering)

    # 3. Assign rIds for non-image parts
    styles_rid = f"rId{next_rid}";    next_rid += 1
    settings_rid = f"rId{next_rid}";  next_rid += 1
    if has_numbering:
        numbering_rid = f"rId{next_rid}"; next_rid += 1
    else:
        numbering_rid = None

    # 4. Collect unique hyperlink URLs and assign rIds
    #    hyperlink_rids: {url → new_rid}
    hyperlink_rids: dict[str, str] = {}
    for link in _collect_hyperlinks(doc):
        if link.url not in hyperlink_rids and not link.url.startswith("#"):
            hyperlink_rids[link.url] = f"rId{next_rid}"
            next_rid += 1

    # 5. Build image_rids map used by document_writer
    image_rids = {orig: info[0] for orig, info in image_info.items()}

    # 6. Assemble document.xml.rels entries
    rel_entries: list[tuple] = []
    for orig_rid, (new_rid, filename, ct, _) in image_info.items():
        rel_entries.append((new_rid, REL_IMAGE, f"media/{filename}"))
    rel_entries.append((styles_rid, REL_STYLES, "styles.xml"))
    rel_entries.append((settings_rid, REL_SETTINGS, "settings.xml"))
    if numbering_rid:
        rel_entries.append((numbering_rid, REL_NUMBERING, "numbering.xml"))
    for url, rid in hyperlink_rids.items():
        rel_entries.append((rid, REL_HYPERLINK, url, "External"))

    # 7. Build image content-type entries for [Content_Types].xml
    ct_image_entries = [
        (f"/word/media/{info[1]}", info[2])
        for info in image_info.values()
    ]

    # 8. Build all XML parts
    doc_xml       = build_document_xml(doc, image_rids, hyperlink_rids)
    styles_xml    = build_styles_xml(doc.styles)
    settings_xml  = build_settings_xml()
    doc_rels_xml  = build_document_rels_xml(rel_entries)
    root_rels_xml = build_root_rels_xml()
    ct_xml        = build_content_types_xml(ct_image_entries, has_numbering)
    numbering_xml = build_numbering_xml(doc.numbering) if has_numbering else None

    # 8. Write ZIP archive
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",         ct_xml)
        zf.writestr("_rels/.rels",                 root_rels_xml)
        zf.writestr("word/document.xml",           doc_xml)
        zf.writestr("word/_rels/document.xml.rels", doc_rels_xml)
        zf.writestr("word/styles.xml",             styles_xml)
        zf.writestr("word/settings.xml",           settings_xml)
        if numbering_xml is not None:
            zf.writestr("word/numbering.xml", numbering_xml)
        for orig_rid, (new_rid, filename, ct, data) in image_info.items():
            zf.writestr(f"word/media/{filename}", data)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Image collection
# ---------------------------------------------------------------------------

def _collect_images(doc: Document) -> list[InlineImage]:
    """Walk the entire body and return all InlineImage objects in order."""
    images: list[InlineImage] = []
    _walk_body(doc.body, images)
    return images


def _walk_body(body, images: list[InlineImage]) -> None:
    for element in body:
        if isinstance(element, Paragraph):
            for run in element.runs:
                if isinstance(run, ImageRun):
                    images.append(run.image)
                elif isinstance(run, Hyperlink):
                    pass  # hyperlinks don't contribute images
        elif isinstance(element, Table):
            for row in element.rows:
                for cell in row.cells:
                    _walk_body(cell.paragraphs, images)


# ---------------------------------------------------------------------------
# Hyperlink collection
# ---------------------------------------------------------------------------

def _collect_hyperlinks(doc: Document) -> list[Hyperlink]:
    """Walk the entire body and return all Hyperlink objects in order."""
    hyperlinks: list[Hyperlink] = []
    _walk_body_hyperlinks(doc.body, hyperlinks)
    return hyperlinks


def _walk_body_hyperlinks(body, hyperlinks: list[Hyperlink]) -> None:
    for element in body:
        if isinstance(element, Paragraph):
            for run in element.runs:
                if isinstance(run, Hyperlink):
                    hyperlinks.append(run)
        elif isinstance(element, Table):
            for row in element.rows:
                for cell in row.cells:
                    _walk_body_hyperlinks(cell.paragraphs, hyperlinks)
