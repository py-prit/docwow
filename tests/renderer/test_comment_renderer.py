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


class TestCommentRefHoverPopup:
    """Inline hover popup emitted when comments lookup is passed."""

    def _comment(self, cid: int, author: str, text: str, date: str = "") -> Comment:
        return Comment(comment_id=cid, author=author, date=date, paragraphs=(_para(text),))

    def test_popup_present_when_comment_provided(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        c = self._comment(1, "Alice", "Great point.")
        para = Paragraph(runs=(CommentRef(comment_id=1),))
        html = render_paragraph(para, comments={1: c})
        assert 'class="dw-comment-popup"' in html
        assert 'class="dw-comment-popup-author"' in html
        assert "Alice" in html
        assert "Great point." in html

    def test_popup_absent_without_comments(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        para = Paragraph(runs=(CommentRef(comment_id=1),))
        html = render_paragraph(para)
        assert 'dw-comment-popup' not in html

    def test_popup_absent_for_unknown_comment_id(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        para = Paragraph(runs=(CommentRef(comment_id=99),))
        html = render_paragraph(para, comments={1: self._comment(1, "Alice", "x")})
        assert 'dw-comment-popup' not in html

    def test_popup_includes_date(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        c = self._comment(2, "Bob", "Fix this.", date="2024-01-15T10:00:00Z")
        para = Paragraph(runs=(CommentRef(comment_id=2),))
        html = render_paragraph(para, comments={2: c})
        assert 'class="dw-comment-popup-date"' in html
        assert "2024-01-15T10:00:00Z" in html

    def test_popup_no_date_span_when_date_empty(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        c = self._comment(3, "Carol", "LGTM")
        para = Paragraph(runs=(CommentRef(comment_id=3),))
        html = render_paragraph(para, comments={3: c})
        assert 'dw-comment-popup-date' not in html

    def test_author_html_escaped(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        c = self._comment(1, "A & B", "ok")
        para = Paragraph(runs=(CommentRef(comment_id=1),))
        html = render_paragraph(para, comments={1: c})
        assert "A &amp; B" in html
        assert "A & B" not in html

    def test_text_html_escaped(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        c = self._comment(1, "A", "<script>alert(1)</script>")
        para = Paragraph(runs=(CommentRef(comment_id=1),))
        html = render_paragraph(para, comments={1: c})
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_data_dw_comment_id_preserved(self):
        from docwow.models.paragraph import CommentRef
        from docwow.renderer.paragraph_renderer import render_paragraph
        c = self._comment(7, "Dave", "Check this.")
        para = Paragraph(runs=(CommentRef(comment_id=7),))
        html = render_paragraph(para, comments={7: c})
        assert 'data-dw-comment-id="7"' in html
