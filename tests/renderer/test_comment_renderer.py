"""Tests for docwow.renderer.comment_renderer."""
from __future__ import annotations

from docwow.models.comment import Comment
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import RunFormatting
from docwow.renderer.comment_renderer import render_comments


def _para(text: str) -> Paragraph:
    return Paragraph(runs=(TextRun(text=text),))


class TestRenderCommentsEmpty:
    def test_empty_tuple(self):
        assert render_comments(()) == ""


class TestRenderCommentsSingle:
    def test_section_element(self):
        c = Comment(comment_id=1, author="Alice", paragraphs=(_para("Nice work."),))
        html = render_comments((c,))
        assert 'class="dw-comments"' in html
        assert 'data-dw-note-section="comments"' in html

    def test_comment_div_id(self):
        c = Comment(comment_id=3, author="Bob", paragraphs=(_para("Fix."),))
        html = render_comments((c,))
        assert 'id="comment-3"' in html
        assert 'data-dw-comment-id="3"' in html

    def test_author_attribute(self):
        c = Comment(comment_id=1, author="Alice Smith", paragraphs=(_para("ok"),))
        html = render_comments((c,))
        assert 'data-dw-comment-author="Alice Smith"' in html

    def test_date_attribute(self):
        c = Comment(comment_id=1, author="A", date="2024-01-15T10:00:00Z", paragraphs=(_para("x"),))
        html = render_comments((c,))
        assert 'data-dw-comment-date="2024-01-15T10:00:00Z"' in html

    def test_initials_attribute(self):
        c = Comment(comment_id=1, author="A", initials="AS", paragraphs=(_para("x"),))
        html = render_comments((c,))
        assert 'data-dw-comment-initials="AS"' in html

    def test_marker_superscript(self):
        c = Comment(comment_id=2, author="A", paragraphs=(_para("x"),))
        html = render_comments((c,))
        assert 'class="dw-comment-marker"' in html
        assert "[2]" in html

    def test_body_div(self):
        c = Comment(comment_id=1, author="A", paragraphs=(_para("Hello"),))
        html = render_comments((c,))
        assert 'class="dw-comment-body"' in html
        assert "Hello" in html


class TestRenderCommentsMultiple:
    def test_two_comments(self):
        comments = (
            Comment(comment_id=1, author="Alice", paragraphs=(_para("First"),)),
            Comment(comment_id=2, author="Bob", paragraphs=(_para("Second"),)),
        )
        html = render_comments(comments)
        assert 'id="comment-1"' in html
        assert 'id="comment-2"' in html
        assert "First" in html
        assert "Second" in html

    def test_section_appears_once(self):
        comments = (
            Comment(comment_id=1, author="A", paragraphs=(_para("x"),)),
            Comment(comment_id=2, author="B", paragraphs=(_para("y"),)),
        )
        html = render_comments(comments)
        assert html.count('<section') == 1
        assert html.count('</section>') == 1


class TestRenderCommentRefInParagraph:
    def test_comment_ref_renders_link(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        para = Paragraph(runs=(TextRun(text="See"), CommentRef(comment_id=5)))
        html = render_paragraph(para)
        assert 'class="dw-comment-ref"' in html
        assert 'data-dw-comment-id="5"' in html
        assert 'href="#comment-5"' in html
        assert "[5]" in html

    def test_comment_ref_does_not_produce_text_run(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        para = Paragraph(runs=(CommentRef(comment_id=1),))
        html = render_paragraph(para)
        assert "dw-comment-ref" in html
        # Should not be wrapped in dw-r span
        assert 'class="dw-r"' not in html
