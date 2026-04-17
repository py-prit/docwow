"""Render comment sections to HTML."""
from __future__ import annotations

import html

from docwow.models.comment import Comment
from docwow.renderer.paragraph_renderer import render_paragraph


def render_comments(comments: tuple[Comment, ...]) -> str:
    """Render comments as a ``<section class="dw-comments">`` block.

    Returns an empty string if *comments* is empty.
    """
    if not comments:
        return ""

    lines: list[str] = ['<section class="dw-comments" data-dw-note-section="comments">']

    for comment in comments:
        author_escaped = html.escape(comment.author, quote=True)
        date_escaped = html.escape(comment.date, quote=True)
        initials_escaped = html.escape(comment.initials, quote=True)
        marker = f'<span class="dw-comment-marker">[{comment.comment_id}]</span>'
        para_html = "\n".join(render_paragraph(p) for p in comment.paragraphs)
        lines.append(
            f'<div class="dw-comment" id="comment-{comment.comment_id}" '
            f'data-dw-comment-id="{comment.comment_id}" '
            f'data-dw-comment-author="{author_escaped}" '
            f'data-dw-comment-date="{date_escaped}" '
            f'data-dw-comment-initials="{initials_escaped}">'
            f"{marker}"
            f'<div class="dw-comment-body">{para_html}</div>'
            f"</div>"
        )

    lines.append("</section>")
    return "\n".join(lines)
