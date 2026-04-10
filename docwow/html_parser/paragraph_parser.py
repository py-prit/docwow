"""Parse <p class="dw-p"> elements into Paragraph model objects."""
from __future__ import annotations

import base64

from docwow.html_parser._utils import has_class, pt_val
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo
from docwow.models.paragraph import ImageRun, Paragraph, Run, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting


def parse_paragraph(p_el) -> Paragraph:
    """Parse a <p class="dw-p"> lxml element into a Paragraph."""
    return Paragraph(
        runs=tuple(_parse_runs(p_el)),
        formatting=_parse_para_formatting(p_el),
        list_info=_parse_list_info(p_el),
    )


# ---------------------------------------------------------------------------
# Paragraph-level
# ---------------------------------------------------------------------------

def _parse_para_formatting(p_el) -> ParagraphFormatting:
    g = p_el.get
    return ParagraphFormatting(
        style_id=g("data-dw-style"),
        alignment=g("data-dw-alignment"),
        indent_left_pt=pt_val(g("data-dw-indent-left"), 0.0),
        indent_right_pt=pt_val(g("data-dw-indent-right"), 0.0),
        indent_first_line_pt=pt_val(g("data-dw-indent-first-line"), 0.0),
        space_before_pt=pt_val(g("data-dw-space-before"), 0.0),
        space_after_pt=pt_val(g("data-dw-space-after"), 0.0),
        line_spacing_pt=pt_val(g("data-dw-line-spacing")),
        keep_together=g("data-dw-keep-together") == "true",
        keep_with_next=g("data-dw-keep-with-next") == "true",
        page_break_before=g("data-dw-page-break-before") == "true",
    )


def _parse_list_info(p_el) -> ListInfo | None:
    num_id = p_el.get("data-dw-num-id")
    if num_id is None:
        return None
    return ListInfo(num_id=num_id, level=int(p_el.get("data-dw-level", "0")))


# ---------------------------------------------------------------------------
# Run-level
# ---------------------------------------------------------------------------

def _parse_runs(p_el) -> list[Run]:
    runs: list[Run] = []
    for child in p_el:
        if child.tag == "span" and has_class(child, "dw-r"):
            runs.append(_parse_text_run(child))
        elif child.tag == "img" and has_class(child, "dw-img"):
            runs.append(_parse_image_run(child))
    return runs


def _parse_text_run(span_el) -> TextRun:
    return TextRun(
        text=_extract_text(span_el),
        formatting=_parse_run_formatting(span_el),
    )


def _extract_text(span_el) -> str:
    """Reconstruct text content, turning <br> elements back into newlines."""
    parts: list[str] = []
    if span_el.text:
        parts.append(span_el.text)
    for child in span_el:
        if child.tag == "br":
            parts.append("\n")
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def _parse_run_formatting(span_el) -> RunFormatting:
    g = span_el.get
    return RunFormatting(
        bold=g("data-dw-bold") == "true",
        italic=g("data-dw-italic") == "true",
        underline=g("data-dw-underline") == "true",
        strike=g("data-dw-strike") == "true",
        font_name=g("data-dw-font-name"),
        font_size_pt=pt_val(g("data-dw-font-size")),
        color=g("data-dw-color"),
        highlight=g("data-dw-highlight"),
        vertical_align=g("data-dw-vertical-align"),
    )


def _parse_image_run(img_el) -> ImageRun:
    width_pt = pt_val(img_el.get("data-dw-width"), 0.0)
    height_pt = pt_val(img_el.get("data-dw-height"), 0.0)
    content_type, data = _parse_data_uri(img_el.get("src", ""))
    return ImageRun(
        image=InlineImage(
            relationship_id=img_el.get("data-dw-rid", ""),
            content_type=content_type,
            data=data,
            width_pt=width_pt,
            height_pt=height_pt,
            alt_text=img_el.get("alt", ""),
        )
    )


def _parse_data_uri(src: str) -> tuple[str, bytes]:
    """Decode a base64 data URI into (content_type, raw_bytes)."""
    if not src.startswith("data:"):
        return ("", b"")
    rest = src[5:]          # "{content_type};base64,{b64}"
    if "," not in rest:
        return ("", b"")
    meta, b64_data = rest.split(",", 1)
    content_type = meta.split(";")[0]
    try:
        return content_type, base64.b64decode(b64_data)
    except Exception:
        return content_type, b""
