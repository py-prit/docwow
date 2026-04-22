"""Build word/styles.xml from the Document.styles tuple."""
from __future__ import annotations

from lxml import etree

from docwow.models.styles import ParagraphFormatting, RunFormatting, Style, TabStop
from docwow.writer._xml import (
    STYLE_NSMAP, W,
    sub, to_bytes, pt_tw, pt_hp,
)

# alignment: model value → OOXML w:jc val
_JC = {"left": "left", "center": "center", "right": "right", "justify": "both"}


def build_styles_xml(styles: tuple[Style, ...]) -> bytes:
    """Build word/styles.xml from the document's style definitions."""
    root = etree.Element(f"{{{W}}}styles", nsmap=STYLE_NSMAP)

    # Minimal docDefaults so Word opens the file cleanly
    doc_defaults = etree.SubElement(root, f"{{{W}}}docDefaults")
    rpr_def = etree.SubElement(doc_defaults, f"{{{W}}}rPrDefault")
    rpr = etree.SubElement(rpr_def, f"{{{W}}}rPr")
    fonts = etree.SubElement(rpr, f"{{{W}}}rFonts")
    fonts.set(f"{{{W}}}ascii", "Calibri")
    fonts.set(f"{{{W}}}hAnsi", "Calibri")
    fonts.set(f"{{{W}}}cs", "Arial")       # fallback for systems without Calibri
    sz = etree.SubElement(rpr, f"{{{W}}}sz")
    sz.set(f"{{{W}}}val", "22")   # 11pt default
    sz_cs = etree.SubElement(rpr, f"{{{W}}}szCs")
    sz_cs.set(f"{{{W}}}val", "22")

    # Always emit a "Normal" base style so Word uses Calibri 11pt by default
    # (without it Word falls back to Times New Roman)
    style_ids = {s.style_id for s in styles}
    if "Normal" not in style_ids:
        _write_normal_style(root)

    for style in styles:
        _write_style(root, style)

    return to_bytes(root)


def _write_normal_style(parent: etree._Element) -> None:
    """Emit the built-in Normal paragraph style (Calibri 11pt, Arial fallback)."""
    el = etree.SubElement(parent, f"{{{W}}}style")
    el.set(f"{{{W}}}type", "paragraph")
    el.set(f"{{{W}}}styleId", "Normal")
    el.set(f"{{{W}}}default", "1")
    name_el = etree.SubElement(el, f"{{{W}}}name")
    name_el.set(f"{{{W}}}val", "Normal")
    rpr = etree.SubElement(el, f"{{{W}}}rPr")
    fonts = etree.SubElement(rpr, f"{{{W}}}rFonts")
    fonts.set(f"{{{W}}}ascii", "Calibri")
    fonts.set(f"{{{W}}}hAnsi", "Calibri")
    fonts.set(f"{{{W}}}cs", "Arial")
    sz = etree.SubElement(rpr, f"{{{W}}}sz")
    sz.set(f"{{{W}}}val", "22")  # 11pt
    sz_cs = etree.SubElement(rpr, f"{{{W}}}szCs")
    sz_cs.set(f"{{{W}}}val", "22")


def _write_style(parent: etree._Element, style: Style) -> None:
    el = etree.SubElement(parent, f"{{{W}}}style")
    el.set(f"{{{W}}}type", style.style_type)
    el.set(f"{{{W}}}styleId", style.style_id)

    name_el = etree.SubElement(el, f"{{{W}}}name")
    name_el.set(f"{{{W}}}val", style.name)

    if style.based_on:
        based = etree.SubElement(el, f"{{{W}}}basedOn")
        based.set(f"{{{W}}}val", style.based_on)

    if style.next_style:
        next_el = etree.SubElement(el, f"{{{W}}}next")
        next_el.set(f"{{{W}}}val", style.next_style)

    if style.paragraph_fmt or style.outline_level is not None:
        ppr = etree.SubElement(el, f"{{{W}}}pPr")
        if style.paragraph_fmt:
            _write_para_fmt(ppr, style.paragraph_fmt)
        if style.outline_level is not None:
            ol = etree.SubElement(ppr, f"{{{W}}}outlineLvl")
            ol.set(f"{{{W}}}val", str(style.outline_level))

    if style.run_fmt:
        rpr = etree.SubElement(el, f"{{{W}}}rPr")
        _write_run_fmt(rpr, style.run_fmt)


def _write_para_fmt(ppr: etree._Element, fmt: ParagraphFormatting, *, skip_keep_flags: bool = False) -> None:
    """Emit paragraph formatting children inside a w:pPr element.

    OOXML schema order: keepNext → keepLines → pageBreakBefore → spacing → ind → jc.
    Pass ``skip_keep_flags=True`` when the caller has already written the keep*
    elements (e.g. document_writer writes them before w:numPr).
    """
    if not skip_keep_flags:
        if fmt.keep_with_next:
            etree.SubElement(ppr, f"{{{W}}}keepNext")
        if fmt.keep_together:
            etree.SubElement(ppr, f"{{{W}}}keepLines")
        if fmt.page_break_before:
            etree.SubElement(ppr, f"{{{W}}}pageBreakBefore")

    # Spacing
    has_spacing = fmt.space_before_pt or fmt.space_after_pt or fmt.line_spacing_pt is not None
    if has_spacing:
        sp = etree.SubElement(ppr, f"{{{W}}}spacing")
        if fmt.space_before_pt:
            sp.set(f"{{{W}}}before", pt_tw(fmt.space_before_pt))
        if fmt.space_after_pt:
            sp.set(f"{{{W}}}after", pt_tw(fmt.space_after_pt))
        if fmt.line_spacing_pt is not None:
            sp.set(f"{{{W}}}line", pt_tw(fmt.line_spacing_pt))
            sp.set(f"{{{W}}}lineRule", "exact")

    # Indents
    has_ind = fmt.indent_left_pt or fmt.indent_right_pt or fmt.indent_first_line_pt
    if has_ind:
        ind = etree.SubElement(ppr, f"{{{W}}}ind")
        if fmt.indent_left_pt:
            ind.set(f"{{{W}}}left", pt_tw(fmt.indent_left_pt))
        if fmt.indent_right_pt:
            ind.set(f"{{{W}}}right", pt_tw(fmt.indent_right_pt))
        if fmt.indent_first_line_pt > 0:
            ind.set(f"{{{W}}}firstLine", pt_tw(fmt.indent_first_line_pt))
        elif fmt.indent_first_line_pt < 0:
            ind.set(f"{{{W}}}hanging", pt_tw(-fmt.indent_first_line_pt))

    if fmt.alignment and fmt.alignment in _JC:
        sub(ppr, "jc", val=_JC[fmt.alignment])

    if fmt.shading:
        shd = etree.SubElement(ppr, f"{{{W}}}shd")
        shd.set(f"{{{W}}}val", "clear")
        shd.set(f"{{{W}}}color", "auto")
        shd.set(f"{{{W}}}fill", fmt.shading)

    if fmt.tab_stops:
        tabs = etree.SubElement(ppr, f"{{{W}}}tabs")
        for stop in fmt.tab_stops:
            tab = etree.SubElement(tabs, f"{{{W}}}tab")
            tab.set(f"{{{W}}}val", stop.alignment)
            tab.set(f"{{{W}}}pos", pt_tw(stop.position_pt))
            if stop.leader:
                tab.set(f"{{{W}}}leader", stop.leader)

    if fmt.borders:
        _write_para_borders(ppr, fmt.borders)


def _write_para_borders(ppr: etree._Element, borders) -> None:
    pBdr = etree.SubElement(ppr, f"{{{W}}}pBdr")
    for xml_name, bd in (
        ("top",    borders.top),
        ("left",   borders.left),
        ("bottom", borders.bottom),
        ("right",  borders.right),
    ):
        if bd is None:
            continue
        el = etree.SubElement(pBdr, f"{{{W}}}{xml_name}")
        el.set(f"{{{W}}}val", bd.style)
        el.set(f"{{{W}}}sz", str(max(0, round(bd.width_pt * 8))))
        el.set(f"{{{W}}}space", "1")
        el.set(f"{{{W}}}color", bd.color or "auto")


def _write_run_fmt(rpr: etree._Element, fmt: RunFormatting) -> None:
    """Emit run formatting children inside a w:rPr element."""
    if fmt.char_style_id:
        rstyle = etree.SubElement(rpr, f"{{{W}}}rStyle")
        rstyle.set(f"{{{W}}}val", fmt.char_style_id)
    if fmt.bold:
        etree.SubElement(rpr, f"{{{W}}}b")
    if fmt.italic:
        etree.SubElement(rpr, f"{{{W}}}i")
    if fmt.underline:
        u = etree.SubElement(rpr, f"{{{W}}}u")
        u.set(f"{{{W}}}val", "single")
    if fmt.strike:
        etree.SubElement(rpr, f"{{{W}}}strike")
    if fmt.small_caps:
        etree.SubElement(rpr, f"{{{W}}}smallCaps")
    if fmt.all_caps:
        etree.SubElement(rpr, f"{{{W}}}caps")
    if fmt.vanish:
        etree.SubElement(rpr, f"{{{W}}}vanish")
    if fmt.font_name:
        fonts = etree.SubElement(rpr, f"{{{W}}}rFonts")
        fonts.set(f"{{{W}}}ascii", fmt.font_name)
        fonts.set(f"{{{W}}}hAnsi", fmt.font_name)
    if fmt.font_size_pt is not None:
        sz = etree.SubElement(rpr, f"{{{W}}}sz")
        sz.set(f"{{{W}}}val", pt_hp(fmt.font_size_pt))
    if fmt.color:
        col = etree.SubElement(rpr, f"{{{W}}}color")
        col.set(f"{{{W}}}val", fmt.color)
    if fmt.highlight:
        hl = etree.SubElement(rpr, f"{{{W}}}highlight")
        hl.set(f"{{{W}}}val", fmt.highlight)
    if fmt.vertical_align:
        va = etree.SubElement(rpr, f"{{{W}}}vertAlign")
        va.set(f"{{{W}}}val", fmt.vertical_align)
