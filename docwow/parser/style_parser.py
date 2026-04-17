"""
Parse word/styles.xml into a tuple of Style objects.

Word styles cascade: a paragraph style can be based on another style
(w:basedOn), and run formatting inherits from the paragraph's linked
character style.  We store the raw based_on ID and leave cascade
resolution to the renderer — the model just holds what the XML says.
"""

from __future__ import annotations

from lxml import etree

from docwow.models.styles import ParagraphFormatting, RunFormatting, Style, TabStop
from docwow.utils.units import half_pt_to_pt, twips_to_pt
from docwow.utils.xml_utils import attrib, find, findall, qn


def parse_styles(styles_xml: bytes) -> tuple[Style, ...]:
    """Parse the raw bytes of word/styles.xml and return all Style objects."""
    root = etree.fromstring(styles_xml)
    return tuple(
        _parse_style(el)
        for el in root.findall(qn("w:style"))
    )


def _parse_style(el: etree._Element) -> Style:
    style_id = attrib(el, "w:styleId") or ""
    style_type = attrib(el, "w:type") or "paragraph"

    name_el = find(el, "w:name")
    name = attrib(name_el, "w:val") or style_id if name_el is not None else style_id

    based_on_el = find(el, "w:basedOn")
    based_on = attrib(based_on_el, "w:val") if based_on_el is not None else None

    para_fmt = _parse_para_fmt(find(el, "w:pPr"))
    run_fmt = _parse_run_fmt(find(el, "w:rPr"))

    return Style(
        style_id=style_id,
        name=name,
        style_type=style_type,
        based_on=based_on,
        paragraph_fmt=para_fmt,
        run_fmt=run_fmt,
    )


def _parse_para_fmt(pPr: etree._Element | None) -> ParagraphFormatting | None:
    if pPr is None:
        return None

    style_id: str | None = None
    style_el = find(pPr, "w:pStyle")
    if style_el is not None:
        style_id = attrib(style_el, "w:val")

    alignment: str | None = None
    jc_el = find(pPr, "w:jc")
    if jc_el is not None:
        raw = attrib(jc_el, "w:val") or ""
        alignment = _normalise_alignment(raw)

    indent_left_pt = 0.0
    indent_right_pt = 0.0
    indent_first_line_pt = 0.0
    ind_el = find(pPr, "w:ind")
    if ind_el is not None:
        indent_left_pt = _twips_or_zero(attrib(ind_el, "w:left"))
        indent_right_pt = _twips_or_zero(attrib(ind_el, "w:right"))
        # firstLine is positive; hanging is negative (stored as positive in XML)
        first = attrib(ind_el, "w:firstLine")
        hanging = attrib(ind_el, "w:hanging")
        if first is not None:
            indent_first_line_pt = twips_to_pt(int(first))
        elif hanging is not None:
            indent_first_line_pt = -twips_to_pt(int(hanging))

    space_before_pt = 0.0
    space_after_pt = 0.0
    line_spacing_pt: float | None = None
    spacing_el = find(pPr, "w:spacing")
    if spacing_el is not None:
        before = attrib(spacing_el, "w:before")
        after = attrib(spacing_el, "w:after")
        line = attrib(spacing_el, "w:line")
        if before is not None:
            space_before_pt = twips_to_pt(int(before))
        if after is not None:
            space_after_pt = twips_to_pt(int(after))
        if line is not None:
            line_spacing_pt = twips_to_pt(int(line))

    keep_together = find(pPr, "w:keepLines") is not None
    keep_with_next = find(pPr, "w:keepNext") is not None
    page_break_before = find(pPr, "w:pageBreakBefore") is not None

    shading: str | None = None
    shd_el = find(pPr, "w:shd")
    if shd_el is not None:
        fill = attrib(shd_el, "w:fill")
        if fill and fill.upper() not in ("AUTO", "FFFFFF", ""):
            shading = fill.upper()

    tab_stops: tuple[TabStop, ...] = ()
    tabs_el = find(pPr, "w:tabs")
    if tabs_el is not None:
        stops = []
        for tab_el in tabs_el.findall(qn("w:tab")):
            val = attrib(tab_el, "w:val") or "left"
            if val in ("clear", "num"):
                continue
            pos_str = attrib(tab_el, "w:pos")
            if pos_str is None:
                continue
            leader_raw = attrib(tab_el, "w:leader")
            leader = leader_raw if leader_raw and leader_raw != "none" else None
            stops.append(TabStop(
                position_pt=twips_to_pt(int(pos_str)),
                alignment=val,
                leader=leader,
            ))
        tab_stops = tuple(stops)

    return ParagraphFormatting(
        style_id=style_id,
        alignment=alignment,
        indent_left_pt=indent_left_pt,
        indent_right_pt=indent_right_pt,
        indent_first_line_pt=indent_first_line_pt,
        space_before_pt=space_before_pt,
        space_after_pt=space_after_pt,
        line_spacing_pt=line_spacing_pt,
        keep_together=keep_together,
        keep_with_next=keep_with_next,
        page_break_before=page_break_before,
        shading=shading,
        tab_stops=tab_stops,
    )


def _parse_run_fmt(rPr: etree._Element | None) -> RunFormatting | None:
    if rPr is None:
        return None

    bold = _toggle(rPr, "w:b")
    italic = _toggle(rPr, "w:i")
    underline = find(rPr, "w:u") is not None and attrib(find(rPr, "w:u"), "w:val") != "none"
    strike = _toggle(rPr, "w:strike")
    small_caps = _toggle(rPr, "w:smallCaps")
    all_caps = _toggle(rPr, "w:caps")

    font_name: str | None = None
    fonts_el = find(rPr, "w:rFonts")
    if fonts_el is not None:
        font_name = (
            attrib(fonts_el, "w:ascii")
            or attrib(fonts_el, "w:hAnsi")
            or attrib(fonts_el, "w:cs")
        )

    font_size_pt: float | None = None
    sz_el = find(rPr, "w:sz")
    if sz_el is not None:
        raw = attrib(sz_el, "w:val")
        if raw is not None:
            font_size_pt = half_pt_to_pt(int(raw))

    color: str | None = None
    color_el = find(rPr, "w:color")
    if color_el is not None:
        val = attrib(color_el, "w:val")
        if val and val.lower() != "auto":
            color = val.upper()

    highlight: str | None = None
    hl_el = find(rPr, "w:highlight")
    if hl_el is not None:
        highlight = attrib(hl_el, "w:val")

    vertical_align: str | None = None
    valign_el = find(rPr, "w:vertAlign")
    if valign_el is not None:
        raw_va = attrib(valign_el, "w:val") or ""
        if raw_va == "superscript":
            vertical_align = "superscript"
        elif raw_va == "subscript":
            vertical_align = "subscript"

    char_style_id: str | None = None
    rstyle_el = find(rPr, "w:rStyle")
    if rstyle_el is not None:
        char_style_id = attrib(rstyle_el, "w:val") or None

    return RunFormatting(
        bold=bold,
        italic=italic,
        underline=underline,
        strike=strike,
        small_caps=small_caps,
        all_caps=all_caps,
        font_name=font_name,
        font_size_pt=font_size_pt,
        color=color,
        highlight=highlight,
        vertical_align=vertical_align,
        char_style_id=char_style_id,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _toggle(rPr: etree._Element, tag: str) -> bool:
    """Return True if *tag* is present and not explicitly set to w:val="0"."""
    el = find(rPr, tag)
    if el is None:
        return False
    val = attrib(el, "w:val")
    return val not in ("0", "false")


def _normalise_alignment(raw: str) -> str | None:
    mapping = {
        "left": "left",
        "start": "left",
        "center": "center",
        "right": "right",
        "end": "right",
        "both": "justify",
        "distribute": "justify",
    }
    return mapping.get(raw.lower())


def _twips_or_zero(val: str | None) -> float:
    if val is None:
        return 0.0
    return twips_to_pt(int(val))


def parse_style_numbering(styles_xml: bytes) -> dict[str, tuple[str, int]]:
    """Return {style_id: (num_id, ilvl)} for styles that embed a w:numPr.

    Word (and python-docx) often puts numbering definitions in the style
    rather than in each paragraph's pPr.  This map lets the body parser
    resolve list membership via the paragraph's applied style.
    """
    root = etree.fromstring(styles_xml)
    result: dict[str, tuple[str, int]] = {}
    for style_el in root.findall(qn("w:style")):
        style_id = attrib(style_el, "w:styleId")
        if not style_id:
            continue
        pPr = find(style_el, "w:pPr")
        if pPr is None:
            continue
        numPr = find(pPr, "w:numPr")
        if numPr is None:
            continue
        ilvl_el = find(numPr, "w:ilvl")
        numId_el = find(numPr, "w:numId")
        ilvl = int(attrib(ilvl_el, "w:val") or "0") if ilvl_el is not None else 0
        num_id = attrib(numId_el, "w:val") if numId_el is not None else None
        if num_id and num_id != "0":
            result[style_id] = (num_id, ilvl)
    return result


# Re-export helpers so body_parser can import them directly
parse_para_fmt = _parse_para_fmt
parse_run_fmt = _parse_run_fmt
