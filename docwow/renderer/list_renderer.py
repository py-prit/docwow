"""
Render consecutive list paragraphs into nested HTML <ul>/<ol> elements.

OOXML list nesting is defined by (num_id, ilvl):
  - Paragraphs with the same num_id belong to the same list.
  - ilvl (0-based) determines nesting depth within that list.
  - Different num_ids are separate, unrelated lists.

The stack-based algorithm opens/closes <ul>/<ol> elements as the
(num_id, level) of successive paragraphs changes.
"""

from __future__ import annotations

from docwow.models.comment import Comment
from docwow.models.lists import NumberingDefinition
from docwow.models.paragraph import Paragraph
from docwow.renderer.paragraph_renderer import render_paragraph


def render_list_group(
    paragraphs: list[Paragraph],
    numbering: tuple[NumberingDefinition, ...],
    comments: dict[int, Comment] | None = None,
) -> str:
    """Render a sequence of list paragraphs (all with list_info set) to HTML.

    Args:
        paragraphs:  Consecutive list Paragraphs to render.
        numbering:   The document's numbering definitions, used to determine
                     whether each list is ordered (ol) or unordered (ul).

    Returns:
        HTML string containing nested <ul>/<ol> elements.
    """
    if not paragraphs:
        return ""

    num_fmt_map = _build_num_fmt_map(numbering)
    buf: list[str] = []
    # Stack entries: (num_id, level, list_tag)
    stack: list[tuple[str, int, str]] = []

    for para in paragraphs:
        assert para.list_info is not None
        num_id = para.list_info.num_id
        level = para.list_info.level
        list_tag = _list_tag(num_id, level, num_fmt_map)

        # Pop stack levels that are deeper than the current item,
        # or that belong to a different list (different num_id at root).
        while stack:
            top_num_id, top_level, top_tag = stack[-1]
            if top_num_id == num_id and top_level <= level:
                break
            # Close this level
            stack.pop()
            buf.append(f"</li></{top_tag}>")

        if not stack or stack[-1][0] != num_id:
            # Start a brand-new list
            buf.append(
                f'<{list_tag} class="dw-list" data-dw-num-id="{num_id}">'
            )
            buf.append(_open_li(num_id, level))
            stack.append((num_id, level, list_tag))

        elif stack[-1][1] < level:
            # Dive deeper into the same list
            buf.append(
                f'<{list_tag} class="dw-list" data-dw-num-id="{num_id}">'
            )
            buf.append(_open_li(num_id, level))
            stack.append((num_id, level, list_tag))

        else:
            # Same num_id and same level: close the previous <li> and open a new one
            buf.append("</li>")
            buf.append(_open_li(num_id, level))

        buf.append(render_paragraph(para, comments=comments))

    # Close all remaining open elements
    while stack:
        _, _, tag = stack.pop()
        buf.append(f"</li></{tag}>")

    return "\n".join(buf)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_li(num_id: str, level: int) -> str:
    return f'<li class="dw-li" data-dw-num-id="{num_id}" data-dw-level="{level}">'


def _build_num_fmt_map(numbering: tuple[NumberingDefinition, ...]) -> dict[str, str]:
    """Build {num_id: num_fmt_of_level_0} for list tag selection."""
    result: dict[str, str] = {}
    for nd in numbering:
        for lvl in nd.levels:
            if lvl.level == 0:
                result[nd.abstract_num_id] = lvl.num_fmt
                break
    return result


def _list_tag(num_id: str, level: int, num_fmt_map: dict[str, str]) -> str:
    """Return 'ol' for ordered lists and 'ul' for unordered (bullet) lists."""
    fmt = num_fmt_map.get(num_id, "bullet")
    ordered_fmts = {"decimal", "lowerLetter", "upperLetter", "lowerRoman", "upperRoman"}
    return "ol" if fmt in ordered_fmts else "ul"
