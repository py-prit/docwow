"""
Parse word/numbering.xml into NumberingDefinition objects.

OOXML numbering is two-layer:
  abstractNum  — the canonical definition of a numbering scheme and its levels
  num          — a concrete instance that references an abstractNum (allows
                 per-document overrides via w:lvlOverride)

We resolve each num → its abstractNum at parse time and return one
NumberingDefinition per concrete num ID, so the rest of the pipeline
only has to deal with num IDs.
"""

from __future__ import annotations

from lxml import etree

from docwow.models.lists import ListLevel, NumberingDefinition
from docwow.parser.style_parser import parse_run_fmt
from docwow.utils.units import twips_to_pt
from docwow.utils.xml_utils import attrib, find, findall, qn


def parse_numbering(numbering_xml: bytes) -> tuple[NumberingDefinition, ...]:
    """Parse word/numbering.xml and return one NumberingDefinition per num."""
    root = etree.fromstring(numbering_xml)

    # Build abstractNum id → list of ListLevel
    abstract: dict[str, list[ListLevel]] = {}
    for an in root.findall(qn("w:abstractNum")):
        an_id = attrib(an, "w:abstractNumId") or ""
        abstract[an_id] = _parse_abstract_levels(an)

    # Build concrete num id → resolved ListLevel tuple
    defs: list[NumberingDefinition] = []
    for num in root.findall(qn("w:num")):
        num_id = attrib(num, "w:numId") or ""
        link = find(num, "w:abstractNumId")
        an_id = attrib(link, "w:val") if link is not None else None
        if an_id is None or an_id not in abstract:
            continue
        levels = tuple(abstract[an_id])
        defs.append(NumberingDefinition(abstract_num_id=num_id, levels=levels))

    return tuple(defs)


def _parse_abstract_levels(an: etree._Element) -> list[ListLevel]:
    levels: list[ListLevel] = []
    for lvl_el in an.findall(qn("w:lvl")):
        level_idx_str = attrib(lvl_el, "w:ilvl") or "0"
        level_idx = int(level_idx_str)

        num_fmt_el = find(lvl_el, "w:numFmt")
        num_fmt = attrib(num_fmt_el, "w:val") or "bullet" if num_fmt_el is not None else "bullet"
        num_fmt = _normalise_num_fmt(num_fmt)

        start_val = 1
        start_el = find(lvl_el, "w:start")
        if start_el is not None:
            raw = attrib(start_el, "w:val")
            if raw is not None:
                start_val = int(raw)

        text_template = "%1."
        lvl_text_el = find(lvl_el, "w:lvlText")
        if lvl_text_el is not None:
            raw_text = attrib(lvl_text_el, "w:val")
            if raw_text is not None:
                text_template = raw_text

        indent_pt = 0.0
        hanging_pt = 0.0
        pPr = find(lvl_el, "w:pPr")
        if pPr is not None:
            ind_el = find(pPr, "w:ind")
            if ind_el is not None:
                left = attrib(ind_el, "w:left")
                hanging = attrib(ind_el, "w:hanging")
                if left is not None:
                    indent_pt = twips_to_pt(int(left))
                if hanging is not None:
                    hanging_pt = twips_to_pt(int(hanging))

        suff_el = find(lvl_el, "w:suff")
        suff = attrib(suff_el, "w:val") or "tab" if suff_el is not None else "tab"

        rPr = find(lvl_el, "w:rPr")
        run_fmt = parse_run_fmt(rPr)

        levels.append(ListLevel(
            level=level_idx,
            num_fmt=num_fmt,
            start_value=start_val,
            text_template=text_template,
            indent_pt=indent_pt,
            hanging_pt=hanging_pt,
            suff=suff,
            run_fmt=run_fmt,
        ))

    return levels


def _normalise_num_fmt(raw: str) -> str:
    mapping = {
        "bullet":       "bullet",
        "decimal":      "decimal",
        "decimalZero":  "decimalZero",
        "lowerLetter":  "lowerLetter",
        "upperLetter":  "upperLetter",
        "lowerRoman":   "lowerRoman",
        "upperRoman":   "upperRoman",
        "none":         "none",
    }
    return mapping.get(raw, "bullet")
