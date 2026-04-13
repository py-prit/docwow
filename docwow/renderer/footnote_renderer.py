"""Render footnote and endnote sections to HTML."""

from __future__ import annotations

from docwow.models.footnote import Footnote
from docwow.renderer.paragraph_renderer import render_paragraph


def render_footnotes(notes: tuple[Footnote, ...]) -> str:
    """Render footnotes as a ``<section class="dw-footnotes">`` block.

    Returns an empty string if *notes* is empty.
    """
    return _render_note_section(notes, note_type="footnote")


def render_endnotes(notes: tuple[Footnote, ...]) -> str:
    """Render endnotes as a ``<section class="dw-endnotes">`` block.

    Returns an empty string if *notes* is empty.
    """
    return _render_note_section(notes, note_type="endnote")


def _render_note_section(notes: tuple[Footnote, ...], note_type: str) -> str:
    if not notes:
        return ""

    section_class = f"dw-{note_type}s"
    item_class = "dw-fn" if note_type == "footnote" else "dw-en"
    marker_class = "dw-fn-marker" if note_type == "footnote" else "dw-en-marker"
    anchor_prefix = "fn" if note_type == "footnote" else "en"
    data_attr = f'data-dw-note-section="{note_type}s"'

    lines: list[str] = [f'<section class="{section_class}" {data_attr}>']

    for note in notes:
        anchor = f"{anchor_prefix}-{note.note_id}"
        marker = f'<span class="{marker_class}">[{note.note_id}]</span>'
        para_html = "\n".join(render_paragraph(p) for p in note.paragraphs)
        lines.append(
            f'<div class="{item_class}" id="{anchor}" '
            f'data-dw-note-id="{note.note_id}" '
            f'data-dw-note-type="{note_type}">'
            f"{marker}"
            f'<div class="dw-fn-body">{para_html}</div>'
            f"</div>"
        )

    lines.append("</section>")
    return "\n".join(lines)
