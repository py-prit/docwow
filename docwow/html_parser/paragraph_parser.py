"""Parse <p class="dw-p"> elements into Paragraph model objects."""
from __future__ import annotations

import base64

from docwow.html_parser._utils import has_class, pt_val
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo
from docwow.models.paragraph import BookmarkStart, CommentRef, FootnoteRef, Hyperlink, ImageRun, PageNumberField, Paragraph, Run, TextRun, TrackedChange
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
        shading=g("data-dw-shading") or None,
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
        elif child.tag == "span" and has_class(child, "dw-field"):
            pf = _parse_page_number_field(child)
            if pf is not None:
                runs.append(pf)
        elif child.tag == "img" and has_class(child, "dw-img"):
            runs.append(_parse_image_run(child))
        elif child.tag == "a" and child.get("data-dw-href"):
            runs.append(_parse_hyperlink(child))
        elif child.tag == "a" and child.get("data-dw-note-id"):
            fn = _parse_footnote_ref(child)
            if fn is not None:
                runs.append(fn)
        elif child.tag == "a" and child.get("data-dw-bookmark"):
            runs.append(BookmarkStart(name=child.get("data-dw-bookmark", "")))
        elif child.tag == "a" and child.get("data-dw-comment-id"):
            cr = _parse_comment_ref(child)
            if cr is not None:
                runs.append(cr)
        elif child.tag == "ins" and has_class(child, "dw-ins"):
            tc = _parse_tracked_change(child, "insert")
            if tc is not None:
                runs.append(tc)
        elif child.tag == "del" and has_class(child, "dw-del"):
            tc = _parse_tracked_change(child, "delete")
            if tc is not None:
                runs.append(tc)
    return runs


def _parse_tracked_change(el, change_type: str) -> TrackedChange | None:
    author = el.get("data-dw-author", "")
    date = el.get("data-dw-date", "")
    try:
        change_id = int(el.get("data-dw-change-id", "0"))
    except ValueError:
        change_id = 0
    inner: list[TextRun | ImageRun] = [
        _parse_text_run(child)
        for child in el
        if child.tag == "span" and has_class(child, "dw-r")
    ]
    if not inner:
        return None
    return TrackedChange(
        change_type=change_type,
        runs=tuple(inner),
        author=author,
        date=date,
        change_id=change_id,
    )


def _parse_comment_ref(a_el) -> CommentRef | None:
    comment_id_str = a_el.get("data-dw-comment-id", "")
    try:
        return CommentRef(comment_id=int(comment_id_str))
    except ValueError:
        return None


def _parse_footnote_ref(a_el) -> FootnoteRef | None:
    note_id_str = a_el.get("data-dw-note-id", "")
    note_type = a_el.get("data-dw-note-type", "footnote")
    try:
        return FootnoteRef(note_id=int(note_id_str), note_type=note_type)
    except ValueError:
        return None


def _parse_page_number_field(span_el) -> PageNumberField | None:
    field_type = span_el.get("data-dw-field", "")
    if not field_type:
        return None
    return PageNumberField(field_type=field_type)


def _parse_hyperlink(a_el) -> Hyperlink:
    url = a_el.get("data-dw-href", "")
    inner_runs = [
        _parse_text_run(child)
        for child in a_el
        if child.tag == "span" and has_class(child, "dw-r")
    ]
    return Hyperlink(url=url, runs=tuple(inner_runs))


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
        char_style_id=g("data-dw-char-style") or None,
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
