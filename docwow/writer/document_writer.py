"""Build word/document.xml from the Document model."""
from __future__ import annotations

from lxml import etree

from docwow.models.document import Document
from docwow.models.image import InlineImage
from docwow.models.paragraph import BookmarkStart, CommentRef, FootnoteRef, Hyperlink, ImageRun, PageBreak, PageNumberField, Paragraph, Run, TextRun, TrackedChange
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.models.table import Table, TableCell, TableRow
from docwow.models.toc import TableOfContents, TocEntry
from docwow.writer._xml import (
    DOC_NSMAP, W, R, WP, A, PIC, XML_SPACE,
    sub, to_bytes, pt_tw, pt_emu, pt_hp,
)
from docwow.writer.styles_writer import _write_para_fmt, _write_run_fmt

_JC = {"left": "left", "center": "center", "right": "right", "justify": "both"}

# Image drawing counter (unique per document build; passed in as state)
# We use a list as a mutable container so nested functions can mutate it.

# Content type → file extension for media naming
_EXTENSIONS: dict[str, str] = {
    "image/png":  ".png",
    "image/jpeg": ".jpg",
    "image/jpg":  ".jpg",
    "image/gif":  ".gif",
    "image/bmp":  ".bmp",
    "image/tiff": ".tiff",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/x-emf": ".emf",
    "image/x-wmf": ".wmf",
}


def build_document_xml(
    doc: Document,
    image_rids: dict[str, str],
    hyperlink_rids: dict[str, str] | None = None,
    hf_rids: dict[tuple[str, str], str] | None = None,
) -> bytes:
    """Build word/document.xml.

    Args:
        doc:            The Document model.
        image_rids:     Mapping ``{original_relationship_id → new_rid}`` for images.
        hyperlink_rids: Mapping ``{url → rid}`` for hyperlink relationships.
        hf_rids:        Mapping ``{("header"|"footer", type) → rid}`` for
                        header/footer relationships (e.g. ``("header", "default") → "rId5"``).

    Returns:
        UTF-8 bytes of the complete document.xml.
    """
    _hyperlink_rids = hyperlink_rids or {}
    root = etree.Element(f"{{{W}}}document", nsmap=DOC_NSMAP)
    body = etree.SubElement(root, f"{{{W}}}body")

    _draw_counter = [1]     # mutable counter for image drawing IDs
    _bookmark_counter = [0]  # mutable counter for w:bookmarkStart/End w:id values

    for element in doc.body:
        if isinstance(element, Paragraph):
            _write_paragraph(body, element, image_rids, _draw_counter, _hyperlink_rids, _bookmark_counter)
        elif isinstance(element, Table):
            _write_table(body, element, image_rids, _draw_counter, _hyperlink_rids, _bookmark_counter)
        elif isinstance(element, TableOfContents):
            _write_toc(body, element)
        elif isinstance(element, PageBreak):
            _write_page_break(body)

    # w:sectPr — page geometry + header/footer references
    _write_sect_pr(body, doc, hf_rids or {})

    return to_bytes(root)


# ---------------------------------------------------------------------------
# Page break
# ---------------------------------------------------------------------------

def _write_page_break(parent: etree._Element) -> None:
    """Write an explicit page break as <w:p><w:r><w:br w:type="page"/></w:r></w:p>."""
    p_el = etree.SubElement(parent, f"{{{W}}}p")
    r_el = etree.SubElement(p_el, f"{{{W}}}r")
    br_el = etree.SubElement(r_el, f"{{{W}}}br")
    br_el.set(f"{{{W}}}type", "page")


# ---------------------------------------------------------------------------
# Table of Contents  (w:sdt)
# ---------------------------------------------------------------------------

def _write_toc(parent: etree._Element, toc: TableOfContents) -> None:
    """Write a :class:`TableOfContents` as a ``w:sdt`` structured document tag."""
    sdt = etree.SubElement(parent, f"{{{W}}}sdt")

    # w:sdtPr — identifies this as a TOC
    sdt_pr = etree.SubElement(sdt, f"{{{W}}}sdtPr")
    tag_el = etree.SubElement(sdt_pr, f"{{{W}}}tag")
    tag_el.set(f"{{{W}}}val", "Table of Contents")
    doc_part_obj = etree.SubElement(sdt_pr, f"{{{W}}}docPartObj")
    gallery = etree.SubElement(doc_part_obj, f"{{{W}}}docPartGallery")
    gallery.set(f"{{{W}}}val", "Table of Contents")
    etree.SubElement(doc_part_obj, f"{{{W}}}docPartUnique")

    # w:sdtContent
    sdt_content = etree.SubElement(sdt, f"{{{W}}}sdtContent")

    # TOC heading paragraph
    if toc.title:
        _write_toc_heading(sdt_content, toc.title)

    # TOC entry paragraphs
    for entry in toc.entries:
        _write_toc_entry(sdt_content, entry)


def _write_toc_heading(parent: etree._Element, title: str) -> None:
    p_el = etree.SubElement(parent, f"{{{W}}}p")
    ppr = etree.SubElement(p_el, f"{{{W}}}pPr")
    sub(ppr, "pStyle", val="TOCHeading")
    r_el = etree.SubElement(p_el, f"{{{W}}}r")
    t_el = etree.SubElement(r_el, f"{{{W}}}t")
    t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t_el.text = title


def _write_toc_entry(parent: etree._Element, entry: TocEntry) -> None:
    p_el = etree.SubElement(parent, f"{{{W}}}p")
    ppr = etree.SubElement(p_el, f"{{{W}}}pPr")
    sub(ppr, "pStyle", val=f"TOC{entry.level}")

    if entry.url and entry.url.startswith("#"):
        anchor = entry.url[1:]
        hl = etree.SubElement(p_el, f"{{{W}}}hyperlink")
        hl.set(f"{{{W}}}anchor", anchor)
        r_el = etree.SubElement(hl, f"{{{W}}}r")
        t_el = etree.SubElement(r_el, f"{{{W}}}t")
        t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t_el.text = entry.text
    else:
        r_el = etree.SubElement(p_el, f"{{{W}}}r")
        t_el = etree.SubElement(r_el, f"{{{W}}}t")
        t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t_el.text = entry.text


# ---------------------------------------------------------------------------
# Paragraph
# ---------------------------------------------------------------------------

def _write_paragraph(
    parent: etree._Element,
    para: Paragraph,
    image_rids: dict[str, str],
    draw_counter: list[int],
    hyperlink_rids: dict[str, str] | None = None,
    bookmark_counter: list[int] | None = None,
) -> None:
    p_el = etree.SubElement(parent, f"{{{W}}}p")
    ppr = etree.SubElement(p_el, f"{{{W}}}pPr")
    fmt = para.formatting

    if fmt.style_id:
        sub(ppr, "pStyle", val=fmt.style_id)

    # OOXML schema: keepNext/keepLines/pageBreakBefore must precede w:numPr
    if fmt.keep_with_next:
        etree.SubElement(ppr, f"{{{W}}}keepNext")
    if fmt.keep_together:
        etree.SubElement(ppr, f"{{{W}}}keepLines")
    if fmt.page_break_before:
        etree.SubElement(ppr, f"{{{W}}}pageBreakBefore")

    if para.list_info is not None:
        num_pr = etree.SubElement(ppr, f"{{{W}}}numPr")
        sub(num_pr, "ilvl", val=str(para.list_info.level))
        sub(num_pr, "numId", val=para.list_info.num_id)

    # spacing, ind, jc — keep flags already written above
    _write_para_fmt(ppr, fmt, skip_keep_flags=True)

    _hl_rids = hyperlink_rids or {}
    _bm_counter = bookmark_counter if bookmark_counter is not None else [0]
    for run in para.runs:
        _write_run(p_el, run, image_rids, draw_counter, _hl_rids, _bm_counter)


# ---------------------------------------------------------------------------
# Run dispatch
# ---------------------------------------------------------------------------

def _write_run(
    parent: etree._Element,
    run: Run,
    image_rids: dict[str, str],
    draw_counter: list[int],
    hyperlink_rids: dict[str, str] | None = None,
    bookmark_counter: list[int] | None = None,
) -> None:
    if isinstance(run, Hyperlink):
        _write_hyperlink(parent, run, hyperlink_rids or {})
    elif isinstance(run, ImageRun):
        _write_image_run(parent, run.image, image_rids, draw_counter)
    elif isinstance(run, PageNumberField):
        _write_page_number_field(parent, run)
    elif isinstance(run, FootnoteRef):
        _write_footnote_ref(parent, run)
    elif isinstance(run, BookmarkStart):
        _bm_counter = bookmark_counter if bookmark_counter is not None else [0]
        _write_bookmark(parent, run, _bm_counter)
    elif isinstance(run, CommentRef):
        _write_comment_ref(parent, run)
    elif isinstance(run, TrackedChange):
        _write_tracked_change(parent, run)
    else:
        _write_text_run(parent, run)


# ---------------------------------------------------------------------------
# Hyperlink
# ---------------------------------------------------------------------------

def _write_hyperlink(
    parent: etree._Element,
    link: Hyperlink,
    hyperlink_rids: dict[str, str],
) -> None:
    hl = etree.SubElement(parent, f"{{{W}}}hyperlink")
    if link.url.startswith("#"):
        hl.set(f"{{{W}}}anchor", link.url[1:])
    else:
        hl.set(f"{{{R}}}id", hyperlink_rids.get(link.url, ""))
    for run in link.runs:
        _write_text_run(hl, run)


# ---------------------------------------------------------------------------
# Bookmark
# ---------------------------------------------------------------------------

def _write_bookmark(
    parent: etree._Element,
    start: BookmarkStart,
    bookmark_counter: list[int],
) -> None:
    """Write <w:bookmarkStart> + <w:bookmarkEnd> as a point anchor."""
    bm_id = str(bookmark_counter[0])
    bookmark_counter[0] += 1

    bm_start = etree.SubElement(parent, f"{{{W}}}bookmarkStart")
    bm_start.set(f"{{{W}}}id", bm_id)
    bm_start.set(f"{{{W}}}name", start.name)

    bm_end = etree.SubElement(parent, f"{{{W}}}bookmarkEnd")
    bm_end.set(f"{{{W}}}id", bm_id)


# ---------------------------------------------------------------------------
# Comment reference
# ---------------------------------------------------------------------------

def _write_comment_ref(parent: etree._Element, ref: CommentRef) -> None:
    """Write the three-element comment reference sequence into a paragraph.

    OOXML requires:
      <w:commentRangeStart w:id="N"/>
      ... (the referenced text would normally go between these) ...
      <w:commentRangeEnd w:id="N"/>
      <w:r>
        <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
        <w:commentReference w:id="N"/>
      </w:r>
    For a point-style reference (no range), the start/end bracket an empty span.
    """
    cid = str(ref.comment_id)

    range_start = etree.SubElement(parent, f"{{{W}}}commentRangeStart")
    range_start.set(f"{{{W}}}id", cid)

    range_end = etree.SubElement(parent, f"{{{W}}}commentRangeEnd")
    range_end.set(f"{{{W}}}id", cid)

    r_el = etree.SubElement(parent, f"{{{W}}}r")
    rpr = etree.SubElement(r_el, f"{{{W}}}rPr")
    rstyle = etree.SubElement(rpr, f"{{{W}}}rStyle")
    rstyle.set(f"{{{W}}}val", "CommentReference")
    comment_ref_el = etree.SubElement(r_el, f"{{{W}}}commentReference")
    comment_ref_el.set(f"{{{W}}}id", cid)


# ---------------------------------------------------------------------------
# Tracked changes
# ---------------------------------------------------------------------------

def _write_tracked_change(parent: etree._Element, tc: TrackedChange) -> None:
    """Write a TrackedChange as ``<w:ins>`` or ``<w:del>``."""
    tag = f"{{{W}}}ins" if tc.change_type == "insert" else f"{{{W}}}del"
    el = etree.SubElement(parent, tag)
    el.set(f"{{{W}}}id", str(tc.change_id))
    el.set(f"{{{W}}}author", tc.author)
    el.set(f"{{{W}}}date", tc.date)

    for run in tc.runs:
        r_el = etree.SubElement(el, f"{{{W}}}r")
        if isinstance(run, TextRun):
            _write_r_rpr(r_el, run.formatting)
            text_tag = f"{{{W}}}delText" if tc.change_type == "delete" else f"{{{W}}}t"
            t_el = etree.SubElement(r_el, text_tag)
            t_el.set(XML_SPACE, "preserve")
            t_el.text = run.text
        elif isinstance(run, ImageRun):
            # Images inside tracked changes are written as normal inline images
            _write_r_rpr(r_el, run.formatting)
            _write_image_run(r_el, run.image, {}, [1])


def _write_r_rpr(r_el: etree._Element, fmt) -> None:
    """Add a <w:rPr> to a run element, removing it if empty."""
    rpr = etree.SubElement(r_el, f"{{{W}}}rPr")
    _write_run_fmt(rpr, fmt)
    if len(rpr) == 0 and not rpr.text:
        r_el.remove(rpr)


# ---------------------------------------------------------------------------
# Page number field
# ---------------------------------------------------------------------------

def _write_page_number_field(parent: etree._Element, field: PageNumberField) -> None:
    """Write a page number field using the complex fldChar form."""
    fmt = field.formatting

    def _run_with_fmt() -> etree._Element:
        r_el = etree.SubElement(parent, f"{{{W}}}r")
        if _has_run_fmt(fmt):
            rpr = etree.SubElement(r_el, f"{{{W}}}rPr")
            _write_run_fmt(rpr, fmt)
        return r_el

    # begin
    r_begin = _run_with_fmt()
    fc_begin = etree.SubElement(r_begin, f"{{{W}}}fldChar")
    fc_begin.set(f"{{{W}}}fldCharType", "begin")

    # instrText
    r_instr = _run_with_fmt()
    instr = etree.SubElement(r_instr, f"{{{W}}}instrText")
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr.text = f" {field.field_type} "

    # separate
    r_sep = _run_with_fmt()
    fc_sep = etree.SubElement(r_sep, f"{{{W}}}fldChar")
    fc_sep.set(f"{{{W}}}fldCharType", "separate")

    # placeholder display value
    r_disp = _run_with_fmt()
    t_el = etree.SubElement(r_disp, f"{{{W}}}t")
    t_el.text = "1"

    # end
    r_end = _run_with_fmt()
    fc_end = etree.SubElement(r_end, f"{{{W}}}fldChar")
    fc_end.set(f"{{{W}}}fldCharType", "end")


# ---------------------------------------------------------------------------
# Footnote / endnote reference
# ---------------------------------------------------------------------------

def _write_footnote_ref(parent: etree._Element, ref: FootnoteRef) -> None:
    """Write a footnote or endnote reference run."""
    r_el = etree.SubElement(parent, f"{{{W}}}r")
    # Mark run with the appropriate reference style
    rpr = etree.SubElement(r_el, f"{{{W}}}rPr")
    rstyle = etree.SubElement(rpr, f"{{{W}}}rStyle")
    style_val = "FootnoteReference" if ref.note_type == "footnote" else "EndnoteReference"
    rstyle.set(f"{{{W}}}val", style_val)

    ref_tag = "footnoteReference" if ref.note_type == "footnote" else "endnoteReference"
    ref_el = etree.SubElement(r_el, f"{{{W}}}{ref_tag}")
    ref_el.set(f"{{{W}}}id", str(ref.note_id))


# ---------------------------------------------------------------------------
# Text run
# ---------------------------------------------------------------------------

def _write_text_run(parent: etree._Element, run: TextRun) -> None:
    r_el = etree.SubElement(parent, f"{{{W}}}r")
    fmt = run.formatting

    # w:rPr (only if there is non-default formatting)
    if _has_run_fmt(fmt):
        rpr = etree.SubElement(r_el, f"{{{W}}}rPr")
        _write_run_fmt(rpr, fmt)

    # Write text, converting embedded newlines to <w:br/>
    _write_text_content(r_el, run.text)


def _has_run_fmt(fmt: RunFormatting) -> bool:
    return any([
        fmt.bold, fmt.italic, fmt.underline, fmt.strike,
        fmt.small_caps, fmt.all_caps,
        fmt.font_name, fmt.font_size_pt is not None,
        fmt.color, fmt.highlight, fmt.vertical_align,
        fmt.char_style_id,
    ])


def _write_text_content(r_el: etree._Element, text: str) -> None:
    """Write text to a run, splitting on \\n→w:br and \\t→w:tab."""
    # Split on newlines first, then on tabs within each segment
    for line_idx, line in enumerate(text.split("\n")):
        if line_idx > 0:
            etree.SubElement(r_el, f"{{{W}}}br")
        segments = line.split("\t")
        _append_t(r_el, segments[0])
        for seg in segments[1:]:
            etree.SubElement(r_el, f"{{{W}}}tab")
            _append_t(r_el, seg)


def _append_t(r_el: etree._Element, text: str) -> None:
    t_el = etree.SubElement(r_el, f"{{{W}}}t")
    t_el.set(XML_SPACE, "preserve")
    t_el.text = text


# ---------------------------------------------------------------------------
# Image run
# ---------------------------------------------------------------------------

def _write_image_run(
    parent: etree._Element,
    image: InlineImage,
    image_rids: dict[str, str],
    draw_counter: list[int],
) -> None:
    new_rid = image_rids.get(image.relationship_id, image.relationship_id)
    draw_id = draw_counter[0]
    draw_counter[0] += 1

    cx = pt_emu(image.width_pt)
    cy = pt_emu(image.height_pt)
    name = f"Image{draw_id}"

    r_el = etree.SubElement(parent, f"{{{W}}}r")
    drawing = etree.SubElement(r_el, f"{{{W}}}drawing")
    inline = etree.SubElement(drawing, f"{{{WP}}}inline")
    inline.set("distT", "0")
    inline.set("distB", "0")
    inline.set("distL", "0")
    inline.set("distR", "0")

    extent = etree.SubElement(inline, f"{{{WP}}}extent")
    extent.set("cx", cx)
    extent.set("cy", cy)

    effect = etree.SubElement(inline, f"{{{WP}}}effectExtent")
    for attr in ("l", "t", "r", "b"):
        effect.set(attr, "0")

    doc_pr = etree.SubElement(inline, f"{{{WP}}}docPr")
    doc_pr.set("id", str(draw_id))
    doc_pr.set("name", name)

    # a:graphic
    graphic = etree.SubElement(inline, f"{{{A}}}graphic")
    gdata = etree.SubElement(graphic, f"{{{A}}}graphicData")
    gdata.set("uri", f"http://schemas.openxmlformats.org/drawingml/2006/picture")

    # pic:pic
    pic_el = etree.SubElement(gdata, f"{{{PIC}}}pic")

    nv_pr = etree.SubElement(pic_el, f"{{{PIC}}}nvPicPr")
    cnv_pr = etree.SubElement(nv_pr, f"{{{PIC}}}cNvPr")
    cnv_pr.set("id", "0")
    cnv_pr.set("name", name)
    etree.SubElement(nv_pr, f"{{{PIC}}}cNvPicPr")

    blip_fill = etree.SubElement(pic_el, f"{{{PIC}}}blipFill")
    blip = etree.SubElement(blip_fill, f"{{{A}}}blip")
    blip.set(f"{{{R}}}embed", new_rid)
    etree.SubElement(blip_fill, f"{{{A}}}stretch").append(
        etree.Element(f"{{{A}}}fillRect")
    )

    sp_pr = etree.SubElement(pic_el, f"{{{PIC}}}spPr")
    xfrm = etree.SubElement(sp_pr, f"{{{A}}}xfrm")
    off = etree.SubElement(xfrm, f"{{{A}}}off")
    off.set("x", "0")
    off.set("y", "0")
    ext = etree.SubElement(xfrm, f"{{{A}}}ext")
    ext.set("cx", cx)
    ext.set("cy", cy)
    prst = etree.SubElement(sp_pr, f"{{{A}}}prstGeom")
    prst.set("prst", "rect")
    etree.SubElement(prst, f"{{{A}}}avLst")


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

def _write_table(
    parent: etree._Element,
    table: Table,
    image_rids: dict[str, str],
    draw_counter: list[int],
    hyperlink_rids: dict[str, str] | None = None,
    bookmark_counter: list[int] | None = None,
) -> None:
    tbl = etree.SubElement(parent, f"{{{W}}}tbl")
    _write_tbl_pr(tbl, table)

    # tblGrid — column widths
    if table.col_widths_pt:
        grid = etree.SubElement(tbl, f"{{{W}}}tblGrid")
        for w_pt in table.col_widths_pt:
            col = etree.SubElement(grid, f"{{{W}}}gridCol")
            col.set(f"{{{W}}}w", pt_tw(w_pt))

    for row in table.rows:
        _write_row(tbl, row, image_rids, draw_counter, hyperlink_rids, bookmark_counter)


def _write_tbl_pr(tbl: etree._Element, table: Table) -> None:
    tpr = etree.SubElement(tbl, f"{{{W}}}tblPr")

    if table.style_id:
        sub(tpr, "tblStyle", val=table.style_id)

    # Width
    if table.width_pt is not None:
        tw = etree.SubElement(tpr, f"{{{W}}}tblW")
        tw.set(f"{{{W}}}w", pt_tw(table.width_pt))
        tw.set(f"{{{W}}}type", "dxa")

    # Default single-line borders so the table is visible
    borders = etree.SubElement(tpr, f"{{{W}}}tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = etree.SubElement(borders, f"{{{W}}}{side}")
        b.set(f"{{{W}}}val", "single")
        b.set(f"{{{W}}}sz", "4")
        b.set(f"{{{W}}}space", "0")
        b.set(f"{{{W}}}color", "auto")


def _write_row(
    tbl: etree._Element,
    row: TableRow,
    image_rids: dict[str, str],
    draw_counter: list[int],
    hyperlink_rids: dict[str, str] | None = None,
    bookmark_counter: list[int] | None = None,
) -> None:
    tr = etree.SubElement(tbl, f"{{{W}}}tr")

    if row.height_pt is not None:
        trpr = etree.SubElement(tr, f"{{{W}}}trPr")
        trh = etree.SubElement(trpr, f"{{{W}}}trHeight")
        trh.set(f"{{{W}}}val", pt_tw(row.height_pt))

    for cell in row.cells:
        _write_cell(tr, cell, image_rids, draw_counter, hyperlink_rids, bookmark_counter)


def _write_cell(
    tr: etree._Element,
    cell: TableCell,
    image_rids: dict[str, str],
    draw_counter: list[int],
    hyperlink_rids: dict[str, str] | None = None,
    bookmark_counter: list[int] | None = None,
) -> None:
    tc = etree.SubElement(tr, f"{{{W}}}tc")
    tcpr = etree.SubElement(tc, f"{{{W}}}tcPr")

    if cell.width_pt is not None:
        tcw = etree.SubElement(tcpr, f"{{{W}}}tcW")
        tcw.set(f"{{{W}}}w", pt_tw(cell.width_pt))
        tcw.set(f"{{{W}}}type", "dxa")

    if cell.col_span > 1:
        gs = etree.SubElement(tcpr, f"{{{W}}}gridSpan")
        gs.set(f"{{{W}}}val", str(cell.col_span))

    if cell.v_merge_start:
        vm = etree.SubElement(tcpr, f"{{{W}}}vMerge")
        vm.set(f"{{{W}}}val", "restart")
    elif cell.v_merge_continue:
        etree.SubElement(tcpr, f"{{{W}}}vMerge")

    if cell.shading:
        shd = etree.SubElement(tcpr, f"{{{W}}}shd")
        shd.set(f"{{{W}}}val", "clear")
        shd.set(f"{{{W}}}color", "auto")
        shd.set(f"{{{W}}}fill", cell.shading)

    # Each cell must have at least one paragraph
    if cell.paragraphs:
        for para in cell.paragraphs:
            _write_paragraph(tc, para, image_rids, draw_counter, hyperlink_rids, bookmark_counter)
    else:
        etree.SubElement(tc, f"{{{W}}}p")


# ---------------------------------------------------------------------------
# Section properties (page geometry)
# ---------------------------------------------------------------------------

def _write_sect_pr(
    body: etree._Element,
    doc,
    hf_rids: dict[tuple[str, str], str],
) -> None:
    """Write <w:sectPr> with page geometry and optional header/footer references."""
    from docwow.writer._xml import R as _R
    sect = etree.SubElement(body, f"{{{W}}}sectPr")

    # Header/footer references must precede pgSz per OOXML schema
    hf_slots = [
        (doc.header_default, "headerReference", "default"),
        (doc.header_first,   "headerReference", "first"),
        (doc.header_even,    "headerReference", "even"),
        (doc.footer_default, "footerReference", "default"),
        (doc.footer_first,   "footerReference", "first"),
        (doc.footer_even,    "footerReference", "even"),
    ]
    for hf, ref_tag, hf_type in hf_slots:
        if hf is not None:
            kind = "header" if ref_tag == "headerReference" else "footer"
            rid = hf_rids.get((kind, hf_type), "")
            ref_el = etree.SubElement(sect, f"{{{W}}}{ref_tag}")
            ref_el.set(f"{{{W}}}type", hf_type)
            ref_el.set(f"{{{_R}}}id", rid)

    if doc.title_pg:
        etree.SubElement(sect, f"{{{W}}}titlePg")

    pgsz = etree.SubElement(sect, f"{{{W}}}pgSz")
    pgsz.set(f"{{{W}}}w", pt_tw(doc.page_width_pt))
    pgsz.set(f"{{{W}}}h", pt_tw(doc.page_height_pt))

    pgmar = etree.SubElement(sect, f"{{{W}}}pgMar")
    pgmar.set(f"{{{W}}}top",    pt_tw(doc.margin_top_pt))
    pgmar.set(f"{{{W}}}right",  pt_tw(doc.margin_right_pt))
    pgmar.set(f"{{{W}}}bottom", pt_tw(doc.margin_bottom_pt))
    pgmar.set(f"{{{W}}}left",   pt_tw(doc.margin_left_pt))
