"""
Parse docwow-generated HTML back into a Document model.

The HTML produced by render_document() encodes all Word metadata in
data-dw-* attributes, so the round-trip is lossless for structure and
formatting.  Styles are reconstructed as minimal Style objects (style_id
and name only); full style declarations are preserved per-paragraph via
the data attributes on each <p> element.
"""
from __future__ import annotations

import json

import lxml.html

from docwow.html_parser._utils import has_class, pt_val
from docwow.html_parser.comment_parser import parse_comments
from docwow.html_parser.paragraph_parser import parse_paragraph
from docwow.html_parser.table_parser import parse_table
from docwow.html_parser.toc_parser import parse_toc
from docwow.models.comment import Comment
from docwow.models.document import Document
from docwow.models.footnote import Footnote
from docwow.models.header_footer import HeaderFooter
from docwow.models.lists import ListLevel, NumberingDefinition
from docwow.models.paragraph import PageBreak, Paragraph
from docwow.models.section import SectionBreak, SectionProperties
from docwow.models.borders import BorderDef
from docwow.models.styles import (
    ParagraphBorders, ParagraphFormatting, RunFormatting, Style, TabStop,
)
from docwow.models.table import Table
from docwow.models.toc import TableOfContents


def parse_html(source: str | bytes) -> Document:
    """Parse a docwow HTML string back into a Document model.

    Args:
        source: HTML produced by ``render_document()``, as a string or
                UTF-8 bytes.

    Returns:
        A :class:`~docwow.models.document.Document` whose body, geometry,
        styles, and numbering reflect the content of the HTML.

    Raises:
        ValueError: If the HTML does not contain a ``dw-document`` element.
    """
    if isinstance(source, str):
        source = source.encode("utf-8")
    root = lxml.html.document_fromstring(source)

    divs = root.xpath('.//div[contains(@class,"dw-document")]')
    if not divs:
        raise ValueError("HTML does not contain a dw-document element")
    doc_div = divs[0]

    # Page geometry — fall back to A4 / 1-inch margins if attributes absent
    g = doc_div.get
    page_width_pt    = pt_val(g("data-dw-page-width"),    595.28)
    page_height_pt   = pt_val(g("data-dw-page-height"),   841.89)
    margin_top_pt    = pt_val(g("data-dw-margin-top"),    72.0)
    margin_bottom_pt = pt_val(g("data-dw-margin-bottom"), 72.0)
    margin_left_pt   = pt_val(g("data-dw-margin-left"),   72.0)
    margin_right_pt  = pt_val(g("data-dw-margin-right"),  72.0)

    style_meta = _parse_style_meta(root)
    body, numbering, style_ids = _parse_body(doc_div)
    title_pg = doc_div.get("data-dw-title-pg") == "true"

    # Merge style_ids from body with all style_ids in style_meta (e.g. TOC styles
    # that aren't directly referenced by paragraphs but define tab stops / formatting)
    all_style_ids = style_ids | set(style_meta.keys())

    styles = tuple(
        _style_from_meta(sid, style_meta.get(sid, {}))
        for sid in sorted(all_style_ids)
    )

    # Headers and footers — parsed from <header>/<footer> siblings of dw-document
    hf_kwargs = _parse_hf_elements(root)

    # Footnotes and endnotes — parsed from <section class="dw-footnotes/endnotes">
    footnotes = _parse_note_section(root, note_type="footnote")
    endnotes = _parse_note_section(root, note_type="endnote")

    # Comments — parsed from <section class="dw-comments">
    comments = _parse_comment_section(root)

    return Document(
        body=body,
        styles=styles,
        numbering=numbering,
        page_width_pt=page_width_pt,
        page_height_pt=page_height_pt,
        margin_top_pt=margin_top_pt,
        margin_bottom_pt=margin_bottom_pt,
        margin_left_pt=margin_left_pt,
        margin_right_pt=margin_right_pt,
        title_pg=title_pg,
        footnotes=footnotes,
        endnotes=endnotes,
        comments=comments,
        **hf_kwargs,
    )


def _parse_style_meta(root) -> dict[str, dict]:
    """Read the style metadata JSON block emitted by the renderer."""
    for script in root.xpath('//script[@type="application/docwow-style-meta"]'):
        text = script.text_content().strip()
        if text:
            try:
                return json.loads(text)
            except Exception:
                pass
    return {}


def _style_from_meta(style_id: str, meta: dict) -> Style:
    """Reconstruct a full Style object from the style_meta JSON entry."""
    return Style(
        style_id=style_id,
        name=meta.get("name", style_id),
        style_type=meta.get("styleType", "paragraph"),
        based_on=meta.get("basedOn"),
        next_style=meta.get("next"),
        outline_level=meta.get("outlineLvl"),
        paragraph_fmt=_dict_to_para_fmt(meta["paraFmt"]) if "paraFmt" in meta else None,
        run_fmt=_dict_to_run_fmt(meta["runFmt"]) if "runFmt" in meta else None,
    )


def _dict_to_para_fmt(d: dict) -> ParagraphFormatting:
    tab_stops: tuple[TabStop, ...] = ()
    if "tabStops" in d:
        tab_stops = tuple(
            TabStop(
                position_pt=ts["pos"],
                alignment=ts["align"],
                leader=ts.get("leader"),
            )
            for ts in d["tabStops"]
        )
    borders = None
    if "borders" in d:
        sides = {}
        for side in ("top", "left", "bottom", "right"):
            bd = d["borders"].get(side)
            if bd:
                sides[side] = BorderDef(
                    style=bd["style"],
                    width_pt=bd["widthPt"],
                    color=bd.get("color"),
                )
        borders = ParagraphBorders(**sides)
    return ParagraphFormatting(
        alignment=d.get("alignment"),
        indent_left_pt=d.get("indentLeft", 0.0),
        indent_right_pt=d.get("indentRight", 0.0),
        indent_first_line_pt=d.get("indentFirstLine", 0.0),
        space_before_pt=d.get("spaceBefore", 0.0),
        space_after_pt=d.get("spaceAfter", 0.0),
        line_spacing_pt=d.get("lineSpacing"),
        keep_together=d.get("keepTogether", False),
        keep_with_next=d.get("keepWithNext", False),
        page_break_before=d.get("pageBreakBefore", False),
        shading=d.get("shading"),
        tab_stops=tab_stops,
        borders=borders,
    )


def _dict_to_run_fmt(d: dict) -> RunFormatting:
    return RunFormatting(
        bold=d.get("bold", False),
        italic=d.get("italic", False),
        underline=d.get("underline", False),
        strike=d.get("strike", False),
        small_caps=d.get("smallCaps", False),
        all_caps=d.get("allCaps", False),
        vanish=d.get("vanish", False),
        font_name=d.get("fontName"),
        font_size_pt=d.get("fontSize"),
        color=d.get("color"),
        highlight=d.get("highlight"),
        vertical_align=d.get("verticalAlign"),
        char_style_id=d.get("charStyleId"),
    )


# ---------------------------------------------------------------------------
# Header / footer parsing
# ---------------------------------------------------------------------------

_HF_FIELD_MAP = {
    ("header", "default"): "header_default",
    ("header", "first"):   "header_first",
    ("header", "even"):    "header_even",
    ("footer", "default"): "footer_default",
    ("footer", "first"):   "footer_first",
    ("footer", "even"):    "footer_even",
}


def _parse_hf_elements(root) -> dict:
    """Find all <header>/<footer class="dw-header/footer"> elements and parse them."""
    result: dict = {}
    body_el = root.find(".//body")
    if body_el is None:
        body_el = root
    for child in body_el:
        tag = child.tag
        if tag not in ("header", "footer"):
            continue
        hf_type = child.get(f"data-dw-{tag}-type", "default")
        key = _HF_FIELD_MAP.get((tag, hf_type))
        if key is None:
            continue
        paragraphs = tuple(
            parse_paragraph(p_el)
            for p_el in child
            if p_el.tag == "p" and has_class(p_el, "dw-p")
        )
        result[key] = HeaderFooter(paragraphs=paragraphs)
    return result


# ---------------------------------------------------------------------------
# Body traversal
# ---------------------------------------------------------------------------

def _parse_body(
    doc_div,
) -> tuple[tuple, tuple[NumberingDefinition, ...], set[str]]:
    """Walk direct children of the dw-document div and build the body tuple."""
    body: list = []
    style_ids: set[str] = set()
    # num_id → {level → ListLevel}
    numbering_levels: dict[str, dict[int, ListLevel]] = {}

    for child in doc_div:
        tag = child.tag
        if tag == "p" and has_class(child, "dw-p"):
            para = parse_paragraph(child)
            body.append(para)
            _collect_style(para, style_ids)

        elif tag == "table" and has_class(child, "dw-table"):
            body.append(parse_table(child))

        elif tag in ("ul", "ol") and has_class(child, "dw-list"):
            _collect_list(child, body, style_ids, numbering_levels)

        elif tag == "nav" and has_class(child, "dw-toc"):
            body.append(parse_toc(child))

        elif tag == "div" and has_class(child, "dw-page-break"):
            body.append(PageBreak())

        elif tag == "div" and has_class(child, "dw-section-break"):
            body.append(_parse_section_break(child))

    return tuple(body), _build_numbering(numbering_levels), style_ids


def _parse_section_break(div_el) -> SectionBreak:
    g = div_el.get
    return SectionBreak(properties=SectionProperties(
        page_width_pt=pt_val(g("data-dw-page-width"), 595.28),
        page_height_pt=pt_val(g("data-dw-page-height"), 841.89),
        margin_top_pt=pt_val(g("data-dw-margin-top"), 72.0),
        margin_bottom_pt=pt_val(g("data-dw-margin-bottom"), 72.0),
        margin_left_pt=pt_val(g("data-dw-margin-left"), 72.0),
        margin_right_pt=pt_val(g("data-dw-margin-right"), 72.0),
        break_type=g("data-dw-break-type") or "nextPage",
    ))


def _collect_list(
    list_el,
    body: list,
    style_ids: set[str],
    numbering_levels: dict[str, dict[int, ListLevel]],
) -> None:
    """Extract paragraphs from a dw-list element, handling nesting."""
    num_id = list_el.get("data-dw-num-id", "")

    for li in list_el:
        if li.tag != "li":
            continue
        level = int(li.get("data-dw-level", "0"))
        if num_id not in numbering_levels or level not in numbering_levels[num_id]:
            lvl_obj = _parse_list_level(list_el, level)
            numbering_levels.setdefault(num_id, {})[level] = lvl_obj

        for child in li:
            if child.tag == "p" and has_class(child, "dw-p"):
                para = parse_paragraph(child)
                body.append(para)
                _collect_style(para, style_ids)
            elif child.tag in ("ul", "ol") and has_class(child, "dw-list"):
                _collect_list(child, body, style_ids, numbering_levels)


def _parse_list_level(list_el, level: int) -> ListLevel:
    """Build a ListLevel from data attributes on a <ul>/<ol> element."""
    default_fmt = "bullet" if list_el.tag == "ul" else "decimal"
    num_fmt = list_el.get("data-dw-num-fmt", default_fmt)
    text_template = list_el.get("data-dw-text-template", "\u2022" if num_fmt == "bullet" else "%1.")
    start_value = int(list_el.get("data-dw-start", "1"))
    suff = list_el.get("data-dw-suff", "tab")

    # Recover label run_fmt from the inline style on the first label span
    run_fmt: RunFormatting | None = None
    first_li = next((c for c in list_el if c.tag == "li"), None)
    if first_li is not None:
        label_spans = first_li.xpath('.//span[contains(@class,"dw-list-label")]')
        if label_spans and label_spans[0].get("style"):
            run_fmt = _css_to_run_fmt(label_spans[0].get("style", ""))

    return ListLevel(
        level=level,
        num_fmt=num_fmt,
        text_template=text_template,
        start_value=start_value,
        suff=suff,
        run_fmt=run_fmt,
    )


def _collect_style(para: Paragraph, style_ids: set[str]) -> None:
    if para.formatting.style_id:
        style_ids.add(para.formatting.style_id)


def _parse_note_section(root, note_type: str) -> tuple[Footnote, ...]:
    """Parse ``<section class="dw-footnotes/endnotes">`` into Footnote objects."""
    section_class = f"dw-{note_type}s"
    item_class = "dw-fn" if note_type == "footnote" else "dw-en"
    sections = root.xpath(f'.//section[contains(@class,"{section_class}")]')
    if not sections:
        return ()

    notes: list[Footnote] = []
    for section in sections:
        for item in section:
            if not has_class(item, item_class):
                continue
            note_id_str = item.get("data-dw-note-id", "")
            try:
                note_id = int(note_id_str)
            except ValueError:
                continue
            # Content is inside .dw-fn-body div
            body_divs = item.xpath('./div[contains(@class,"dw-fn-body")]')
            paragraphs = []
            for body_div in body_divs:
                for p_el in body_div:
                    if p_el.tag == "p" and has_class(p_el, "dw-p"):
                        paragraphs.append(parse_paragraph(p_el))
            notes.append(Footnote(
                note_id=note_id,
                paragraphs=tuple(paragraphs),
                note_type=note_type,
            ))

    return tuple(notes)


def _parse_comment_section(root) -> tuple[Comment, ...]:
    """Parse ``<section class="dw-comments">`` into Comment objects."""
    sections = root.xpath('.//section[contains(@class,"dw-comments")]')
    if not sections:
        return ()
    return parse_comments(sections[0])


def _build_numbering(
    numbering_levels: dict[str, dict[int, ListLevel]],
) -> tuple[NumberingDefinition, ...]:
    return tuple(
        NumberingDefinition(
            abstract_num_id=num_id,
            levels=tuple(lvl_obj for _, lvl_obj in sorted(levels.items())),
        )
        for num_id, levels in sorted(numbering_levels.items())
    )


def _css_to_run_fmt(style: str) -> RunFormatting | None:
    """Parse an inline CSS style string into a RunFormatting object."""
    props: dict[str, str] = {}
    for part in style.split(";"):
        part = part.strip()
        if ":" in part:
            k, _, v = part.partition(":")
            props[k.strip()] = v.strip()
    if not props:
        return None
    bold = props.get("font-weight") == "bold"
    italic = props.get("font-style") == "italic"
    td = props.get("text-decoration", "")
    underline = "underline" in td
    strike = "line-through" in td
    font_name = props.get("font-family")
    font_size_pt: float | None = None
    raw_size = props.get("font-size", "")
    if raw_size.endswith("pt"):
        try:
            font_size_pt = float(raw_size[:-2])
        except ValueError:
            pass
    color = props.get("color", "").lstrip("#") or None
    if not any([bold, italic, underline, strike, font_name, font_size_pt, color]):
        return None
    return RunFormatting(
        bold=bold, italic=italic, underline=underline, strike=strike,
        font_name=font_name, font_size_pt=font_size_pt, color=color,
    )
