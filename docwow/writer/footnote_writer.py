"""Write word/footnotes.xml and word/endnotes.xml from Footnote models."""
from __future__ import annotations

from lxml import etree

from docwow.models.footnote import Footnote
from docwow.writer._xml import W, DOC_NSMAP, sub, to_bytes


def write_footnotes(notes: tuple[Footnote, ...]) -> bytes:
    """Return the bytes of ``word/footnotes.xml``."""
    return _write_note_part(notes, note_type="footnote")


def write_endnotes(notes: tuple[Footnote, ...]) -> bytes:
    """Return the bytes of ``word/endnotes.xml``."""
    return _write_note_part(notes, note_type="endnote")


def _write_note_part(notes: tuple[Footnote, ...], note_type: str) -> bytes:
    root_tag = "footnotes" if note_type == "footnote" else "endnotes"
    note_tag = "footnote" if note_type == "footnote" else "endnote"
    ref_tag = "footnoteRef" if note_type == "footnote" else "endnoteRef"
    sep_style = "FootnoteText" if note_type == "footnote" else "EndnoteText"

    root = etree.Element(f"{{{W}}}{root_tag}", nsmap=DOC_NSMAP)

    # OOXML requires separator pseudo-notes with id=-1 and id=0
    _write_separator(root, note_tag, note_id=-1, sep_type="separator")
    _write_separator(root, note_tag, note_id=0,  sep_type="continuationSeparator")

    for note in notes:
        note_el = etree.SubElement(root, f"{{{W}}}{note_tag}")
        note_el.set(f"{{{W}}}id", str(note.note_id))

        for para in note.paragraphs:
            _write_note_paragraph(note_el, para, ref_tag, sep_style)

    return to_bytes(root)


def _write_separator(root: etree._Element, note_tag: str, note_id: int, sep_type: str) -> None:
    el = etree.SubElement(root, f"{{{W}}}{note_tag}")
    el.set(f"{{{W}}}type", "separator" if sep_type == "separator" else "continuationSeparator")
    el.set(f"{{{W}}}id", str(note_id))
    p = etree.SubElement(el, f"{{{W}}}p")
    r = etree.SubElement(p, f"{{{W}}}r")
    etree.SubElement(r, f"{{{W}}}{sep_type}")


def _write_note_paragraph(
    note_el: etree._Element,
    para,
    ref_tag: str,
    style_name: str,
) -> None:
    """Write a frozen Paragraph into a footnote/endnote element."""
    from docwow.models.paragraph import FootnoteRef, Hyperlink, ImageRun, PageNumberField, TextRun
    from docwow.writer.document_writer import _write_run
    from docwow.writer._xml import DOC_NSMAP

    p_el = etree.SubElement(note_el, f"{{{W}}}p")

    # Paragraph properties: use the note style
    ppr = etree.SubElement(p_el, f"{{{W}}}pPr")
    pstyle = etree.SubElement(ppr, f"{{{W}}}pStyle")
    pstyle.set(f"{{{W}}}val", style_name)

    # Write the auto-number marker as the first run
    r_marker = etree.SubElement(p_el, f"{{{W}}}r")
    rpr_m = etree.SubElement(r_marker, f"{{{W}}}rPr")
    rstyle_m = etree.SubElement(rpr_m, f"{{{W}}}rStyle")
    rstyle_m.set(f"{{{W}}}val", style_name.replace("Text", "Reference"))
    etree.SubElement(r_marker, f"{{{W}}}{ref_tag}")

    # Write remaining runs (skip any FootnoteRef run — the marker above replaces it)
    image_rids: dict[str, str] = {}
    draw_counter: list[int] = [1]
    for run in para.runs:
        if isinstance(run, FootnoteRef):
            continue  # marker already written above
        _write_run(p_el, run, image_rids, draw_counter, None)
