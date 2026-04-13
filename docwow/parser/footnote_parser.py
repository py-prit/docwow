"""Parse word/footnotes.xml and word/endnotes.xml into Footnote models."""
from __future__ import annotations

import zipfile

from docwow.models.footnote import Footnote
from docwow.utils.xml_utils import parse_xml, qn

# IDs -1 and 0 are OOXML-internal separator pseudo-footnotes; skip them.
_SKIP_IDS = {-1, 0}


def parse_footnotes(
    xml_bytes: bytes,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    note_type: str = "footnote",
) -> tuple[Footnote, ...]:
    """Parse a footnotes or endnotes XML part and return a tuple of Footnote objects.

    Args:
        xml_bytes: Raw bytes of ``word/footnotes.xml`` or ``word/endnotes.xml``.
        zf: The open ZipFile (for image relationships).
        relationships: rId → target mapping from ``document.xml.rels``.
        note_type: ``"footnote"`` or ``"endnote"``.
    """
    from docwow.parser.body_parser import _parse_paragraph

    root = parse_xml(xml_bytes)
    tag = qn("w:footnote") if note_type == "footnote" else qn("w:endnote")
    notes: list[Footnote] = []

    for child in root:
        if child.tag != tag:
            continue
        note_id_str = child.get(qn("w:id"), "")
        try:
            note_id = int(note_id_str)
        except ValueError:
            continue
        if note_id in _SKIP_IDS:
            continue

        paragraphs = []
        for p_el in child:
            if p_el.tag == qn("w:p"):
                paragraphs.append(_parse_paragraph(p_el, zf, relationships, {}))

        notes.append(Footnote(
            note_id=note_id,
            paragraphs=tuple(paragraphs),
            note_type=note_type,
        ))

    return tuple(notes)
