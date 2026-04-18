"""Build word/numbering.xml from the Document.numbering tuple."""
from __future__ import annotations

from lxml import etree

from docwow.models.lists import ListLevel, NumberingDefinition
from docwow.writer._xml import NUM_NSMAP, W, sub, to_bytes, pt_tw

# Default lvlText per num_fmt
_LVL_TEXT: dict[str, str] = {
    "bullet":      "\u2022",   # •
    "decimal":     "%1.",
    "lowerLetter": "%1.",
    "upperLetter": "%1.",
    "lowerRoman":  "%1.",
    "upperRoman":  "%1.",
    "none":        "",
}

# Default indent per level (in pt), mirrors Word's defaults
_DEFAULT_INDENT_PT = 36.0   # 0.5 inch per level
_DEFAULT_HANGING_PT = 18.0  # bullet/number protrudes 0.25 inch


def build_numbering_xml(numbering: tuple[NumberingDefinition, ...]) -> bytes:
    """Build word/numbering.xml from numbering definitions."""
    root = etree.Element(f"{{{W}}}numbering", nsmap=NUM_NSMAP)

    for nd in numbering:
        _write_abstract_num(root, nd)

    # <w:num> elements link concrete numId → abstractNum
    for nd in numbering:
        num_el = etree.SubElement(root, f"{{{W}}}num")
        num_el.set(f"{{{W}}}numId", nd.abstract_num_id)
        abs_ref = etree.SubElement(num_el, f"{{{W}}}abstractNumId")
        abs_ref.set(f"{{{W}}}val", nd.abstract_num_id)

    return to_bytes(root)


def _write_abstract_num(
    parent: etree._Element, nd: NumberingDefinition
) -> None:
    abs_el = etree.SubElement(parent, f"{{{W}}}abstractNum")
    abs_el.set(f"{{{W}}}abstractNumId", nd.abstract_num_id)

    ml = etree.SubElement(abs_el, f"{{{W}}}multiLevelType")
    ml.set(f"{{{W}}}val", "hybridMultilevel")

    for lvl in nd.levels:
        _write_level(abs_el, lvl)


def _write_level(parent: etree._Element, lvl: ListLevel) -> None:
    lvl_el = etree.SubElement(parent, f"{{{W}}}lvl")
    lvl_el.set(f"{{{W}}}ilvl", str(lvl.level))

    start = etree.SubElement(lvl_el, f"{{{W}}}start")
    start.set(f"{{{W}}}val", str(lvl.start_value))

    fmt = etree.SubElement(lvl_el, f"{{{W}}}numFmt")
    fmt.set(f"{{{W}}}val", lvl.num_fmt)

    txt = etree.SubElement(lvl_el, f"{{{W}}}lvlText")
    # Use text_template when it's been set to something format-specific (not the
    # generic "%1." default), otherwise fall back to the format's canonical text.
    default = _LVL_TEXT.get(lvl.num_fmt, "%1.")
    lv_text = lvl.text_template if lvl.text_template != "%1." else default
    txt.set(f"{{{W}}}val", lv_text)

    jc = etree.SubElement(lvl_el, f"{{{W}}}lvlJc")
    jc.set(f"{{{W}}}val", "left")

    # Indentation for this level
    ppr = etree.SubElement(lvl_el, f"{{{W}}}pPr")
    ind = etree.SubElement(ppr, f"{{{W}}}ind")
    left_pt = lvl.indent_pt if lvl.indent_pt else _DEFAULT_INDENT_PT * (lvl.level + 1)
    hanging_pt = lvl.hanging_pt if lvl.hanging_pt else _DEFAULT_HANGING_PT
    ind.set(f"{{{W}}}left", pt_tw(left_pt))
    ind.set(f"{{{W}}}hanging", pt_tw(hanging_pt))

    # Run formatting on the list label
    if lvl.run_fmt:
        from docwow.writer.styles_writer import _write_run_fmt
        rpr = etree.SubElement(lvl_el, f"{{{W}}}rPr")
        _write_run_fmt(rpr, lvl.run_fmt)
