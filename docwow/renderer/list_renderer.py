"""
Render consecutive list paragraphs into nested HTML <ul>/<ol> elements.

OOXML list nesting is defined by (num_id, ilvl):
  - Paragraphs with the same num_id belong to the same list.
  - ilvl (0-based) determines nesting depth within that list.
  - Different num_ids are separate, unrelated lists.

The stack-based algorithm opens/closes <ul>/<ol> elements as the
(num_id, level) of successive paragraphs changes.

Labels are rendered explicitly using the NumberingDefinition's text_template
so that custom formats like "ARTICLE %1" appear correctly instead of relying
on browser CSS list counters.
"""

from __future__ import annotations

from docwow.models.comment import Comment
from docwow.models.lists import ListLevel, NumberingDefinition
from docwow.models.paragraph import Paragraph
from docwow.renderer.paragraph_renderer import render_paragraph


def render_list_group(
    paragraphs: list[Paragraph],
    numbering: tuple[NumberingDefinition, ...],
    comments: dict[int, Comment] | None = None,
    counters: dict[str, dict[int, int]] | None = None,
) -> str:
    """Render a sequence of list paragraphs (all with list_info set) to HTML."""
    if not paragraphs:
        return ""

    num_def_map = {nd.abstract_num_id: nd for nd in numbering}
    # counters[num_id][level] → current count (1-based); caller may pass a
    # persistent dict so counters survive across non-list paragraph breaks.
    if counters is None:
        counters = {}

    buf: list[str] = []
    # Stack entries: (num_id, level, list_tag)
    stack: list[tuple[str, int, str]] = []

    for para in paragraphs:
        assert para.list_info is not None
        num_id = para.list_info.num_id
        level = para.list_info.level
        nd = num_def_map.get(num_id)
        list_tag = _list_tag(nd, level)

        # Pop stack levels that are deeper than the current item,
        # or that belong to a different list (different num_id at root).
        while stack:
            top_num_id, top_level, top_tag = stack[-1]
            if top_num_id == num_id and top_level <= level:
                break
            stack.pop()
            buf.append(f"</li></{top_tag}>")

        if not stack or stack[-1][0] != num_id:
            buf.append(_open_list(list_tag, num_id, level, nd))
            buf.append(_open_li(num_id, level, nd))
            stack.append((num_id, level, list_tag))

        elif stack[-1][1] < level:
            buf.append(_open_list(list_tag, num_id, level, nd))
            buf.append(_open_li(num_id, level, nd))
            stack.append((num_id, level, list_tag))

        else:
            buf.append("</li>")
            buf.append(_open_li(num_id, level, nd))

        # Advance counter for this (num_id, level)
        if num_id not in counters:
            counters[num_id] = {}
        counters[num_id][level] = counters[num_id].get(level, 0) + 1
        # Reset deeper levels when we're at this level
        for deeper in list(counters[num_id].keys()):
            if deeper > level:
                del counters[num_id][deeper]

        label = _make_label(nd, level, counters[num_id])
        lvl_def = _get_level(nd, level) if nd else None
        buf.append(render_paragraph(
            para, comments=comments,
            list_label=label or None,
            list_label_fmt=lvl_def.run_fmt if lvl_def else None,
        ))

    while stack:
        _, _, tag = stack.pop()
        buf.append(f"</li></{tag}>")

    return "\n".join(buf)


# ---------------------------------------------------------------------------
# Label generation
# ---------------------------------------------------------------------------

def _make_label(nd: NumberingDefinition | None, level: int, counters: dict[int, int]) -> str:
    """Generate the rendered label text, e.g. 'ARTICLE I', '1.', '(a)'."""
    if nd is None:
        return ""
    lvl = _get_level(nd, level)
    if lvl is None:
        return ""
    template = lvl.text_template
    if not template or lvl.num_fmt == "bullet":
        return template or ""

    # Expand %N placeholders: %1 = level 0, %2 = level 1, etc.
    result = template
    for ref_level in range(level + 1):
        placeholder = f"%{ref_level + 1}"
        if placeholder in result:
            ref_nd_level = _get_level(nd, ref_level)
            ref_fmt = ref_nd_level.num_fmt if ref_nd_level else "decimal"
            count = counters.get(ref_level, 1)
            start = ref_nd_level.start_value if ref_nd_level else 1
            n = count + start - 1
            result = result.replace(placeholder, _format_counter(n, ref_fmt))
    return result


def _format_counter(n: int, num_fmt: str) -> str:
    if num_fmt == "decimal":
        return str(n)
    if num_fmt == "decimalZero":
        return f"{n:02d}"
    if num_fmt == "upperRoman":
        return _to_roman(n).upper()
    if num_fmt == "lowerRoman":
        return _to_roman(n).lower()
    if num_fmt == "upperLetter":
        return _to_letter(n).upper()
    if num_fmt == "lowerLetter":
        return _to_letter(n).lower()
    return str(n)


def _to_roman(n: int) -> str:
    if n <= 0:
        return str(n)
    vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    result = ""
    for val, sym in zip(vals, syms):
        while n >= val:
            result += sym
            n -= val
    return result


def _to_letter(n: int) -> str:
    if n <= 0:
        return str(n)
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(ord("a") + rem) + result
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_list(tag: str, num_id: str, level: int, nd: NumberingDefinition | None) -> str:
    """Open a <ul>/<ol> with numbering metadata as data attributes."""
    attrs = f'class="dw-list" data-dw-num-id="{num_id}"'
    if nd is not None:
        lvl = _get_level(nd, level)
        if lvl is not None:
            import html as _html
            attrs += f' data-dw-text-template="{_html.escape(lvl.text_template)}"'
            attrs += f' data-dw-num-fmt="{lvl.num_fmt}"'
            attrs += f' data-dw-start="{lvl.start_value}"'
            if lvl.suff != "tab":
                attrs += f' data-dw-suff="{lvl.suff}"'
    return f"<{tag} {attrs}>"


def _open_li(num_id: str, level: int, nd: NumberingDefinition | None = None) -> str:
    style = ""
    if nd is not None:
        lvl = _get_level(nd, level)
        if lvl and lvl.indent_pt:
            style = f' style="padding-left:{lvl.indent_pt}pt"'
    return f'<li class="dw-li" data-dw-num-id="{num_id}" data-dw-level="{level}"{style}>'


def _get_level(nd: NumberingDefinition, level: int) -> ListLevel | None:
    for lvl in nd.levels:
        if lvl.level == level:
            return lvl
    return None


def _list_tag(nd: NumberingDefinition | None, level: int) -> str:
    if nd is None:
        return "ul"
    lvl = _get_level(nd, level)
    if lvl is None:
        return "ul"
    ordered_fmts = {"decimal", "lowerLetter", "upperLetter", "lowerRoman", "upperRoman"}
    return "ol" if lvl.num_fmt in ordered_fmts else "ul"
