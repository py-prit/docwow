"""Write word/comments.xml from Comment models."""
from __future__ import annotations

from lxml import etree

from docwow.models.comment import Comment
from docwow.writer._xml import W, DOC_NSMAP, sub, to_bytes


def write_comments(comments: tuple[Comment, ...]) -> bytes:
    """Return the bytes of ``word/comments.xml``."""
    root = etree.Element(f"{{{W}}}comments", nsmap=DOC_NSMAP)

    for comment in comments:
        comment_el = etree.SubElement(root, f"{{{W}}}comment")
        comment_el.set(f"{{{W}}}id", str(comment.comment_id))
        comment_el.set(f"{{{W}}}author", comment.author)
        if comment.date:
            comment_el.set(f"{{{W}}}date", comment.date)
        if comment.initials:
            comment_el.set(f"{{{W}}}initials", comment.initials)

        for para in comment.paragraphs:
            _write_comment_paragraph(comment_el, para)

    return to_bytes(root)


def _write_comment_paragraph(comment_el: etree._Element, para) -> None:
    """Write a frozen Paragraph into a comment element."""
    from docwow.models.paragraph import CommentRef, FootnoteRef, Hyperlink, ImageRun, PageNumberField, TextRun
    from docwow.writer.document_writer import _write_run
    from docwow.writer._xml import DOC_NSMAP

    p_el = etree.SubElement(comment_el, f"{{{W}}}p")

    # Paragraph properties: use the CommentText style
    ppr = etree.SubElement(p_el, f"{{{W}}}pPr")
    pstyle = etree.SubElement(ppr, f"{{{W}}}pStyle")
    pstyle.set(f"{{{W}}}val", "CommentText")

    # Write the annotation ref marker as the first run
    r_marker = etree.SubElement(p_el, f"{{{W}}}r")
    rpr_m = etree.SubElement(r_marker, f"{{{W}}}rPr")
    rstyle_m = etree.SubElement(rpr_m, f"{{{W}}}rStyle")
    rstyle_m.set(f"{{{W}}}val", "CommentReference")
    etree.SubElement(r_marker, f"{{{W}}}annotationRef")

    image_rids: dict[str, str] = {}
    draw_counter: list[int] = [1]
    for run in para.runs:
        if isinstance(run, CommentRef):
            continue  # marker already written above
        _write_run(p_el, run, image_rids, draw_counter, None)
