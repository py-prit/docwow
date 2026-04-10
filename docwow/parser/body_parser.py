"""
Parse the <w:body> element of word/document.xml into BodyElement objects.

Handles (v0.1):
  - Paragraphs (w:p) — including list paragraphs
  - Tables (w:tbl)
  - Inline images (w:drawing inside w:r)

Unknown top-level elements are skipped silently.
"""

from __future__ import annotations

import zipfile

from lxml import etree

from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo
from docwow.models.paragraph import ImageRun, Paragraph, Run, TextRun
from docwow.models.table import Table, TableCell, TableRow
from docwow.parser.image_parser import extract_image
from docwow.parser.style_parser import parse_para_fmt, parse_run_fmt
from docwow.utils.units import emu_to_pt
from docwow.utils.xml_utils import attrib, find, findall, qn


def parse_body(
    body: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    style_num_map: dict[str, tuple[str, int]] | None = None,
) -> tuple:
    """Parse <w:body> and return a tuple of BodyElement (Paragraph | Table).

    Args:
        style_num_map: Mapping of style_id → (num_id, ilvl) for styles that
                       embed their numbering definition.  Built by
                       style_parser.parse_style_numbering() and used to
                       resolve list membership when a paragraph's own pPr
                       has no w:numPr (the common python-docx / Word pattern).
    """
    _style_num_map = style_num_map or {}
    elements = []
    for child in body:
        tag = child.tag
        if tag == qn("w:p"):
            elements.append(_parse_paragraph(child, zf, relationships, _style_num_map))
        elif tag == qn("w:tbl"):
            elements.append(_parse_table(child, zf, relationships, _style_num_map))
        # w:sectPr and unknown elements are intentionally skipped
    return tuple(elements)


# ---------------------------------------------------------------------------
# Paragraph
# ---------------------------------------------------------------------------

def _parse_paragraph(
    p_el: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    style_num_map: dict[str, tuple[str, int]] | None = None,
) -> Paragraph:
    pPr = find(p_el, "w:pPr")
    formatting = parse_para_fmt(pPr)

    list_info: ListInfo | None = None
    if pPr is not None:
        list_info = _parse_list_info(pPr, style_num_map or {})

    runs: list[Run] = []
    for child in p_el:
        if child.tag == qn("w:r"):
            runs.extend(_parse_run(child, zf, relationships))
        elif child.tag == qn("w:hyperlink"):
            # Flatten hyperlink runs (v0.1 — href not preserved yet)
            for r_el in child.findall(qn("w:r")):
                runs.extend(_parse_run(r_el, zf, relationships))

    from docwow.models.styles import ParagraphFormatting
    return Paragraph(
        runs=tuple(runs),
        formatting=formatting if formatting is not None else ParagraphFormatting(),
        list_info=list_info,
    )


def _parse_list_info(
    pPr: etree._Element,
    style_num_map: dict[str, tuple[str, int]],
) -> ListInfo | None:
    # First: check for an explicit numPr on the paragraph itself
    numPr = find(pPr, "w:numPr")
    if numPr is not None:
        ilvl_el = find(numPr, "w:ilvl")
        numId_el = find(numPr, "w:numId")
        if ilvl_el is not None and numId_el is not None:
            level = int(attrib(ilvl_el, "w:val") or "0")
            num_id = attrib(numId_el, "w:val") or "0"
            if num_id != "0":
                return ListInfo(num_id=num_id, level=level)

    # Fallback: numPr may be embedded in the applied paragraph style
    style_el = find(pPr, "w:pStyle")
    if style_el is not None:
        style_id = attrib(style_el, "w:val")
        if style_id and style_id in style_num_map:
            num_id, level = style_num_map[style_id]
            return ListInfo(num_id=num_id, level=level)

    return None


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def _parse_run(
    r_el: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
) -> list[Run]:
    """Parse a single <w:r> element.

    A run normally produces one TextRun.  If it contains a drawing (inline
    image), it produces one ImageRun instead.  Returns a list because a run
    with both text and a drawing is theoretically possible (though rare).
    """
    rPr = find(r_el, "w:rPr")
    formatting = parse_run_fmt(rPr)

    from docwow.models.styles import RunFormatting
    fmt = formatting if formatting is not None else RunFormatting()

    result: list[Run] = []

    for child in r_el:
        tag = child.tag

        if tag == qn("w:t"):
            text = child.text or ""
            result.append(TextRun(text=text, formatting=fmt))

        elif tag == qn("w:drawing"):
            image = _parse_drawing(child, zf, relationships)
            if image is not None:
                result.append(ImageRun(image=image, formatting=fmt))

        elif tag == qn("w:br"):
            # Line break — represent as a newline TextRun
            br_type = attrib(child, "w:type")
            if br_type in (None, "textWrapping"):
                result.append(TextRun(text="\n", formatting=fmt))
            # Page/column breaks are skipped in v0.1

    return result


# ---------------------------------------------------------------------------
# Drawing / inline image
# ---------------------------------------------------------------------------

def _parse_drawing(
    drawing: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
) -> InlineImage | None:
    # Both wp:inline and wp:anchor contain the same child structure
    inline = find(drawing, "wp:inline")
    if inline is None:
        inline = find(drawing, "wp:anchor")
    if inline is None:
        return None

    # Dimensions from wp:extent
    extent = find(inline, "wp:extent")
    if extent is None:
        return None
    cx = int(attrib(extent, "cx") or "0")
    cy = int(attrib(extent, "cy") or "0")

    # Alt text from wp:docPr
    docPr = find(inline, "wp:docPr")
    alt_text = attrib(docPr, "descr") or attrib(docPr, "title") or "" if docPr is not None else ""

    # rId from a:blip inside pic:blipFill inside pic:pic inside p:graphicData
    blip = _find_blip(inline)
    if blip is None:
        return None
    rid = attrib(blip, "r:embed")
    if rid is None:
        return None

    return extract_image(zf, rid, relationships, cx, cy, alt_text)


def _find_blip(inline: etree._Element) -> etree._Element | None:
    """Traverse the DrawingML tree to find the a:blip element."""
    graphic = find(inline, "a:graphic")
    if graphic is None:
        return None
    graphic_data = find(graphic, "a:graphicData")
    if graphic_data is None:
        return None
    # pic:pic > pic:blipFill > a:blip
    pic_pic = find(graphic_data, "pic:pic")
    if pic_pic is None:
        return None
    blip_fill = find(pic_pic, "pic:blipFill")
    if blip_fill is None:
        return None
    return find(blip_fill, "a:blip")


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def _parse_table(
    tbl: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    style_num_map: dict[str, tuple[str, int]] | None = None,
) -> Table:
    style_id: str | None = None
    tblPr = find(tbl, "w:tblPr")
    if tblPr is not None:
        tblStyle = find(tblPr, "w:tblStyle")
        if tblStyle is not None:
            style_id = attrib(tblStyle, "w:val")

    # Parse column widths from w:tblGrid
    col_widths: list[float] = []
    tblGrid = find(tbl, "w:tblGrid")
    if tblGrid is not None:
        for gridCol in tblGrid.findall(qn("w:gridCol")):
            w_val = attrib(gridCol, "w:w")
            if w_val is not None:
                from docwow.utils.units import twips_to_pt
                col_widths.append(twips_to_pt(int(w_val)))

    rows: list[TableRow] = []
    for tr_el in tbl.findall(qn("w:tr")):
        rows.append(_parse_row(tr_el, zf, relationships, style_num_map))

    return Table(
        rows=tuple(rows),
        col_widths_pt=tuple(col_widths),
        style_id=style_id,
    )


def _parse_row(
    tr_el: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    style_num_map: dict[str, tuple[str, int]] | None = None,
) -> TableRow:
    height_pt: float | None = None
    trPr = find(tr_el, "w:trPr")
    if trPr is not None:
        trHeight = find(trPr, "w:trHeight")
        if trHeight is not None:
            h_val = attrib(trHeight, "w:val")
            if h_val is not None:
                from docwow.utils.units import twips_to_pt
                height_pt = twips_to_pt(int(h_val))

    cells: list[TableCell] = []
    for tc_el in tr_el.findall(qn("w:tc")):
        cells.append(_parse_cell(tc_el, zf, relationships, style_num_map))

    return TableRow(cells=tuple(cells), height_pt=height_pt)


def _parse_cell(
    tc_el: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    style_num_map: dict[str, tuple[str, int]] | None = None,
) -> TableCell:
    col_span = 1
    row_span = 1
    width_pt: float | None = None
    v_merge_start = False
    v_merge_continue = False

    tcPr = find(tc_el, "w:tcPr")
    if tcPr is not None:
        # Width
        tcW = find(tcPr, "w:tcW")
        if tcW is not None:
            w_val = attrib(tcW, "w:w")
            w_type = attrib(tcW, "w:type")
            if w_val is not None and w_type != "nil":
                from docwow.utils.units import twips_to_pt
                width_pt = twips_to_pt(int(w_val))

        # Horizontal span (gridSpan)
        gridSpan = find(tcPr, "w:gridSpan")
        if gridSpan is not None:
            val = attrib(gridSpan, "w:val")
            if val is not None:
                col_span = int(val)

        # Vertical merge
        vMerge = find(tcPr, "w:vMerge")
        if vMerge is not None:
            merge_val = attrib(vMerge, "w:val")
            if merge_val == "restart":
                v_merge_start = True
            else:
                v_merge_continue = True

    paragraphs = tuple(
        _parse_paragraph(p_el, zf, relationships, style_num_map)
        for p_el in tc_el.findall(qn("w:p"))
    )

    return TableCell(
        paragraphs=paragraphs,
        col_span=col_span,
        row_span=row_span,
        width_pt=width_pt,
        v_merge_start=v_merge_start,
        v_merge_continue=v_merge_continue,
    )
