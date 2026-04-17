"""Tests for HTML → Comment round-trip parsing."""
from __future__ import annotations

import lxml.html

from docwow.html_parser.comment_parser import parse_comments
from docwow.html_parser.html_parser import parse_html
from docwow.models.comment import Comment
from docwow.models.paragraph import CommentRef, Paragraph, TextRun
from docwow.renderer.comment_renderer import render_comments
from docwow.renderer.html_renderer import render_document
from docwow.models.document import Document


def _make_doc(**kwargs) -> Document:
    from docwow.models.styles import ParagraphFormatting
    return Document(body=(), styles=(), numbering=(), **kwargs)


class TestParseCommentsSection:
    def _parse(self, html: str) -> tuple:
        root = lxml.html.document_fromstring(html.encode())
        sections = root.xpath('.//section[contains(@class,"dw-comments")]')
        if not sections:
            return ()
        return parse_comments(sections[0])

    def test_empty_section(self):
        html = '<section class="dw-comments" data-dw-note-section="comments"></section>'
        result = self._parse(html)
        assert result == ()

    def test_single_comment(self):
        html = (
            '<section class="dw-comments" data-dw-note-section="comments">'
            '<div class="dw-comment" id="comment-1" data-dw-comment-id="1" '
            'data-dw-comment-author="Alice" data-dw-comment-date="2024-01-15T10:00:00Z" '
            'data-dw-comment-initials="A">'
            '<span class="dw-comment-marker">[1]</span>'
            '<div class="dw-comment-body">'
            '<p class="dw-p"><span class="dw-r">Great idea!</span></p>'
            '</div>'
            '</div>'
            '</section>'
        )
        result = self._parse(html)
        assert len(result) == 1
        c = result[0]
        assert c.comment_id == 1
        assert c.author == "Alice"
        assert c.date == "2024-01-15T10:00:00Z"
        assert c.initials == "A"
        assert len(c.paragraphs) == 1

    def test_two_comments(self):
        html = (
            '<section class="dw-comments">'
            '<div class="dw-comment" data-dw-comment-id="1" data-dw-comment-author="A" '
            'data-dw-comment-date="" data-dw-comment-initials="">'
            '<div class="dw-comment-body"><p class="dw-p"><span class="dw-r">First</span></p></div>'
            '</div>'
            '<div class="dw-comment" data-dw-comment-id="2" data-dw-comment-author="B" '
            'data-dw-comment-date="" data-dw-comment-initials="">'
            '<div class="dw-comment-body"><p class="dw-p"><span class="dw-r">Second</span></p></div>'
            '</div>'
            '</section>'
        )
        result = self._parse(html)
        assert len(result) == 2
        assert result[0].comment_id == 1
        assert result[1].comment_id == 2

    def test_invalid_id_skipped(self):
        html = (
            '<section class="dw-comments">'
            '<div class="dw-comment" data-dw-comment-id="bad" data-dw-comment-author="X" '
            'data-dw-comment-date="" data-dw-comment-initials="">'
            '<div class="dw-comment-body"><p class="dw-p"><span class="dw-r">x</span></p></div>'
            '</div>'
            '</section>'
        )
        result = self._parse(html)
        assert result == ()


class TestCommentRefInParagraphParser:
    def test_comment_ref_parsed(self):
        html = (
            "<!DOCTYPE html><html><body>"
            '<div class="dw-document" data-dw-page-width="595.28pt" data-dw-page-height="841.89pt" '
            'data-dw-margin-top="72pt" data-dw-margin-bottom="72pt" '
            'data-dw-margin-left="72pt" data-dw-margin-right="72pt">'
            '<p class="dw-p">'
            '<span class="dw-r">text</span>'
            '<a href="#comment-3" class="dw-comment-ref" data-dw-comment-id="3">[3]</a>'
            '</p>'
            '</div>'
            '<section class="dw-comments" data-dw-note-section="comments">'
            '<div class="dw-comment" data-dw-comment-id="3" data-dw-comment-author="Alice" '
            'data-dw-comment-date="" data-dw-comment-initials="">'
            '<div class="dw-comment-body"><p class="dw-p"><span class="dw-r">Comment text</span></p></div>'
            '</div>'
            '</section>'
            "</body></html>"
        )
        doc = parse_html(html)
        assert len(doc.body) == 1
        para = doc.body[0]
        assert isinstance(para, Paragraph)
        refs = [r for r in para.runs if isinstance(r, CommentRef)]
        assert len(refs) == 1
        assert refs[0].comment_id == 3
        assert len(doc.comments) == 1
        assert doc.comments[0].comment_id == 3
        assert doc.comments[0].author == "Alice"


class TestCommentRoundTrip:
    def test_render_then_parse_preserves_comments(self):
        from docwow.models.paragraph import CommentRef, TextRun
        from docwow.models.styles import ParagraphFormatting

        para = Paragraph(runs=(TextRun(text="See"), CommentRef(comment_id=1)))
        comment = Comment(
            comment_id=1,
            author="Alice",
            date="2024-06-01T09:00:00Z",
            initials="A",
            paragraphs=(Paragraph(runs=(TextRun(text="Nice work!"),)),),
        )
        doc = Document(
            body=(para,),
            styles=(),
            numbering=(),
            comments=(comment,),
        )

        from docwow.renderer.html_renderer import render_document
        html = render_document(doc)
        parsed = parse_html(html)

        assert len(parsed.comments) == 1
        c = parsed.comments[0]
        assert c.comment_id == 1
        assert c.author == "Alice"
        assert c.date == "2024-06-01T09:00:00Z"
        assert c.initials == "A"

        assert len(parsed.body) == 1
        refs = [r for r in parsed.body[0].runs if isinstance(r, CommentRef)]
        assert len(refs) == 1
        assert refs[0].comment_id == 1
