"""Parse <section class="dw-comments"> elements into Comment models."""
from __future__ import annotations

from docwow.models.comment import Comment
from docwow.html_parser.paragraph_parser import parse_paragraph


def parse_comments(section_el) -> tuple[Comment, ...]:
    """Parse a ``<section class="dw-comments">`` element into a tuple of Comments.

    Args:
        section_el: An lxml element with ``class="dw-comments"``.
    """
    comments: list[Comment] = []

    for child in section_el:
        if child.tag != "div":
            continue
        comment_id_str = child.get("data-dw-comment-id", "")
        try:
            comment_id = int(comment_id_str)
        except ValueError:
            continue

        author = child.get("data-dw-comment-author", "")
        date = child.get("data-dw-comment-date", "")
        initials = child.get("data-dw-comment-initials", "")

        paragraphs = []
        body_div = None
        for grandchild in child:
            if grandchild.tag == "div" and "dw-comment-body" in grandchild.get("class", ""):
                body_div = grandchild
                break

        if body_div is not None:
            for p_el in body_div:
                if p_el.tag == "p" and "dw-p" in p_el.get("class", ""):
                    paragraphs.append(parse_paragraph(p_el))

        comments.append(Comment(
            comment_id=comment_id,
            author=author,
            date=date,
            initials=initials,
            paragraphs=tuple(paragraphs),
        ))

    return tuple(comments)
