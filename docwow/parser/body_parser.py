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
from docwow.models.paragraph import BookmarkStart, CommentRef, FootnoteRef, Hyperlink, ImageRun, PageBreak, PageNumberField, Paragraph, Run, TextRun
from docwow.models.table import Table, TableCell, TableRow
from docwow.models.toc import TableOfContents, TocEntry
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
            if _is_page_break_paragraph(child):
                elements.append(PageBreak())
            else:
                elements.append(_parse_paragraph(child, zf, relationships, _style_num_map))
        elif tag == qn("w:tbl"):
            elements.append(_parse_table(child, zf, relationships, _style_num_map))
        elif tag == qn("w:sdt"):
            toc = _parse_sdt_toc(child, zf, relationships, _style_num_map)
            if toc is not None:
                elements.append(toc)
        # w:sectPr and unknown elements are intentionally skipped
    return tuple(elements)


def _is_page_break_paragraph(p_el: etree._Element) -> bool:
    """Return True if this paragraph contains only an explicit page break and nothing else."""
    runs = []
    for child in p_el:
        if child.tag == qn("w:r"):
            runs.append(child)
        elif child.tag not in (qn("w:pPr"),):
            # Any non-pPr, non-run child (e.g. hyperlink, bookmark) → not a bare page break
            return False
    if not runs:
        return False
    # All runs must contain only a <w:br w:type="page"/> and nothing else
    for r in runs:
        r_children = [c for c in r if c.tag != qn("w:rPr")]
        if len(r_children) != 1:
            return False
        br = r_children[0]
        if br.tag != qn("w:br"):
            return False
        if attrib(br, "w:type") != "page":
            return False
    return True


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
    # State for complex field (fldChar begin…end sequences)
    _field_state: dict | None = None

    for child in p_el:
        tag = child.tag

        if tag == qn("w:r"):
            # Check for complex field characters
            fld_char_el = find(child, "w:fldChar")
            instr_el = find(child, "w:instrText")

            if fld_char_el is not None:
                fld_char_type = attrib(fld_char_el, "w:fldCharType")
                if fld_char_type == "begin":
                    rPr = find(child, "w:rPr")
                    _field_state = {"instr": "", "fmt": parse_run_fmt(rPr)}
                elif fld_char_type == "end":
                    if _field_state is not None:
                        pf = _make_page_number_field(
                            _field_state["instr"], _field_state["fmt"]
                        )
                        if pf is not None:
                            runs.append(pf)
                        _field_state = None
                # "separate" and others: do nothing
                continue

            if instr_el is not None:
                if _field_state is not None:
                    _field_state["instr"] += instr_el.text or ""
                continue

            # Skip display-value runs between "separate" and "end"
            if _field_state is not None:
                continue

            runs.extend(_parse_run(child, zf, relationships))

        elif tag == qn("w:fldSimple"):
            # Simple field form: <w:fldSimple w:instr=" PAGE ">
            pf = _parse_field_simple(child)
            if pf is not None:
                runs.append(pf)

        elif tag == qn("w:hyperlink"):
            hyperlink = _parse_hyperlink(child, zf, relationships)
            if hyperlink is not None:
                runs.append(hyperlink)
            else:
                # No URL found — flatten to plain runs
                for r_el in child.findall(qn("w:r")):
                    runs.extend(_parse_run(r_el, zf, relationships))

        elif tag == qn("w:bookmarkStart"):
            name = attrib(child, "w:name")
            # Skip only the Word-internal navigation bookmark; preserve everything
            # else including _Toc... anchors used by table-of-contents entries.
            if name and name != "_GoBack":
                runs.append(BookmarkStart(name=name))
            # w:bookmarkEnd carries only the numeric ID (no name) and is skipped;
            # the matching end element is synthesised by the writer on round-trip.

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
# Hyperlink
# ---------------------------------------------------------------------------

def _parse_hyperlink(
    hl_el: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
) -> Hyperlink | None:
    """Parse a <w:hyperlink> element into a Hyperlink model.

    Returns None if no URL can be resolved (hyperlink is dropped).
    """
    # External link: r:id → URL from relationships
    r_id = attrib(hl_el, "r:id")
    if r_id:
        url = relationships.get(r_id)
        if url and url.startswith(("http://", "https://", "mailto:", "ftp://")):
            inner_runs = _parse_hyperlink_runs(hl_el, zf, relationships)
            if inner_runs:
                return Hyperlink(url=url, runs=tuple(inner_runs))
            return None

    # Internal anchor link: w:anchor → #anchor
    anchor = attrib(hl_el, "w:anchor")
    if anchor:
        inner_runs = _parse_hyperlink_runs(hl_el, zf, relationships)
        if inner_runs:
            return Hyperlink(url=f"#{anchor}", runs=tuple(inner_runs))

    return None


def _parse_hyperlink_runs(
    hl_el: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
) -> list[TextRun]:
    """Extract text runs from inside a <w:hyperlink> element."""
    result: list[TextRun] = []
    for r_el in hl_el.findall(qn("w:r")):
        for run in _parse_run(r_el, zf, relationships):
            if isinstance(run, TextRun):
                result.append(run)
    return result


# ---------------------------------------------------------------------------
# Page number fields
# ---------------------------------------------------------------------------

_KNOWN_FIELDS = ("PAGE", "NUMPAGES", "SECTIONPAGES")


def _make_page_number_field(instr: str, fmt) -> PageNumberField | None:
    """Return a PageNumberField for known field types, or None."""
    from docwow.models.styles import RunFormatting
    instr_upper = instr.strip().upper()
    for field_type in _KNOWN_FIELDS:
        if instr_upper.startswith(field_type):
            return PageNumberField(
                field_type=field_type,
                formatting=fmt if fmt is not None else RunFormatting(),
            )
    return None


def _parse_field_simple(el: etree._Element) -> PageNumberField | None:
    """Parse a <w:fldSimple> element into a PageNumberField."""
    instr = attrib(el, "w:instr") or ""
    return _make_page_number_field(instr, None)


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
            br_type = attrib(child, "w:type")
            if br_type in (None, "textWrapping"):
                result.append(TextRun(text="\n", formatting=fmt))
            # Page breaks handled at paragraph level by _is_page_break_paragraph

        elif tag == qn("w:footnoteReference"):
            note_id_str = attrib(child, "w:id") or ""
            try:
                result.append(FootnoteRef(note_id=int(note_id_str), note_type="footnote"))
            except ValueError:
                pass

        elif tag == qn("w:endnoteReference"):
            note_id_str = attrib(child, "w:id") or ""
            try:
                result.append(FootnoteRef(note_id=int(note_id_str), note_type="endnote"))
            except ValueError:
                pass

        elif tag == qn("w:commentReference"):
            comment_id_str = attrib(child, "w:id") or ""
            try:
                result.append(CommentRef(comment_id=int(comment_id_str)))
            except ValueError:
                pass

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
# TOC  (w:sdt structured document tag)
# ---------------------------------------------------------------------------

_TOC_STYLE_RE_STR = r'^TOC\d$'
_TOC_HEADING_STYLE = "TOCHeading"
_TOC_ENTRY_PREFIX = "TOC"

import re as _re
_TOC_ENTRY_RE = _re.compile(r'^TOC(\d)$')


def _parse_sdt_toc(
    sdt: etree._Element,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
    style_num_map: dict[str, tuple[str, int]] | None = None,
) -> TableOfContents | None:
    """Try to parse a ``w:sdt`` element as a Table of Contents.

    Returns ``None`` if the structured document tag is not a TOC.
    """
    sdt_content = find(sdt, "w:sdtContent")
    if sdt_content is None:
        return None

    # Collect all paragraphs inside sdtContent
    p_elements = list(sdt_content.iter(qn("w:p")))
    if not p_elements:
        return None

    # Determine if this sdt is a TOC by inspecting paragraph styles
    if not _is_toc_sdt(sdt, p_elements):
        return None

    title = ""
    entries: list[TocEntry] = []

    for p_el in p_elements:
        style_id = _get_para_style(p_el)
        if style_id == _TOC_HEADING_STYLE:
            title = _extract_plain_text(p_el)
        else:
            m = _TOC_ENTRY_RE.match(style_id or "")
            if m:
                level = int(m.group(1))
                text, url = _extract_toc_entry(p_el)
                entries.append(TocEntry(text=text, url=url, level=level))

    return TableOfContents(title=title, entries=tuple(entries))


def _is_toc_sdt(
    sdt: etree._Element,
    p_elements: list[etree._Element],
) -> bool:
    """Return True if this structured document tag looks like a TOC."""
    # Check w:sdtPr/w:tag or w:sdtPr/w:docPartObj/w:docPartGallery
    sdt_pr = find(sdt, "w:sdtPr")
    if sdt_pr is not None:
        tag_el = find(sdt_pr, "w:tag")
        if tag_el is not None:
            tag_val = (attrib(tag_el, "w:val") or "").lower()
            if "toc" in tag_val or "contents" in tag_val or "table of contents" in tag_val:
                return True
        # w:docPartObj/w:docPartGallery
        doc_part_obj = find(sdt_pr, "w:docPartObj")
        if doc_part_obj is not None:
            gallery = find(doc_part_obj, "w:docPartGallery")
            if gallery is not None:
                gallery_val = (attrib(gallery, "w:val") or "").lower()
                if "table of contents" in gallery_val or "toc" in gallery_val:
                    return True

    # Fall back: does any paragraph in the content use a TOC style?
    for p_el in p_elements:
        style_id = _get_para_style(p_el)
        if style_id == _TOC_HEADING_STYLE or _TOC_ENTRY_RE.match(style_id or ""):
            return True

    return False


def _get_para_style(p_el: etree._Element) -> str | None:
    """Return the paragraph style ID or None."""
    pPr = find(p_el, "w:pPr")
    if pPr is None:
        return None
    pStyle = find(pPr, "w:pStyle")
    if pStyle is None:
        return None
    return attrib(pStyle, "w:val")


def _extract_plain_text(p_el: etree._Element) -> str:
    """Extract all text content from a paragraph element."""
    parts: list[str] = []
    for t_el in p_el.iter(qn("w:t")):
        parts.append(t_el.text or "")
    return "".join(parts)


def _extract_toc_entry(p_el: etree._Element) -> tuple[str, str]:
    """Extract (display text, url) from a TOC entry paragraph.

    TOC entries are hyperlinks with w:anchor pointing to ``_Toc…`` bookmarks.
    We prefer the first hyperlink's anchor as the URL; fall back to plain text.
    """
    url = ""
    # Look for a w:hyperlink inside the paragraph
    for hl in p_el.iter(qn("w:hyperlink")):
        anchor = attrib(hl, "w:anchor")
        if anchor:
            url = f"#{anchor}"
            break

    text = _extract_plain_text(p_el)
    return text, url


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
