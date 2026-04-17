"""Parse word/comments.xml into Comment models."""
from __future__ import annotations

import zipfile

from docwow.models.comment import Comment
from docwow.utils.xml_utils import attrib, parse_xml, qn


def parse_comments(
    xml_bytes: bytes,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
) -> tuple[Comment, ...]:
    """Parse ``word/comments.xml`` and return a tuple of Comment objects.

    Args:
        xml_bytes:     Raw bytes of ``word/comments.xml``.
        zf:            The open ZipFile (for image relationships).
        relationships: rId → target mapping from ``document.xml.rels``.
    """
    from docwow.parser.body_parser import _parse_paragraph

    root = parse_xml(xml_bytes)
    comment_tag = qn("w:comment")
    comments: list[Comment] = []

    for child in root:
        if child.tag != comment_tag:
            continue
        comment_id_str = child.get(qn("w:id"), "")
        try:
            comment_id = int(comment_id_str)
        except ValueError:
            continue

        author = child.get(qn("w:author"), "")
        date = child.get(qn("w:date"), "")
        initials = child.get(qn("w:initials"), "")

        paragraphs = []
        for p_el in child:
            if p_el.tag == qn("w:p"):
                paragraphs.append(_parse_paragraph(p_el, zf, relationships, {}))

        comments.append(Comment(
            comment_id=comment_id,
            author=author,
            date=date,
            initials=initials,
            paragraphs=tuple(paragraphs),
        ))

    return tuple(comments)
