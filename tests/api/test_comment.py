"""Tests for docwow.api.comment — MutableComment and MutableCommentRef."""
from __future__ import annotations

import pytest

from docwow.api.comment import MutableComment, MutableCommentRef
from docwow.models.comment import Comment
from docwow.models.paragraph import CommentRef


class TestMutableCommentConstruction:
    def test_defaults(self):
        c = MutableComment(comment_id=1)
        assert c.comment_id == 1
        assert c.author == ""
        assert c.date == ""
        assert c.initials == ""
        assert len(list(c.paragraphs)) == 0

    def test_all_args(self):
        c = MutableComment(comment_id=3, author="Alice", date="2024-01-15T10:00:00Z", initials="A")
        assert c.author == "Alice"
        assert c.date == "2024-01-15T10:00:00Z"
        assert c.initials == "A"


class TestMutableCommentSetters:
    def test_set_author_chainable(self):
        c = MutableComment(comment_id=1)
        result = c.set_author("Bob")
        assert result is c
        assert c.author == "Bob"

    def test_set_date_chainable(self):
        c = MutableComment(comment_id=1)
        result = c.set_date("2024-06-01T00:00:00Z")
        assert result is c
        assert c.date == "2024-06-01T00:00:00Z"

    def test_set_initials_chainable(self):
        c = MutableComment(comment_id=1)
        result = c.set_initials("BB")
        assert result is c
        assert c.initials == "BB"


class TestMutableCommentParagraphs:
    def test_add_paragraph(self):
        c = MutableComment(comment_id=1)
        c.paragraphs.add_paragraph("Hello comment")
        assert c.get_text() == "Hello comment"

    def test_get_text_multiple_paras(self):
        c = MutableComment(comment_id=1)
        c.paragraphs.add_paragraph("Line one")
        c.paragraphs.add_paragraph("Line two")
        text = c.get_text()
        assert "Line one" in text
        assert "Line two" in text


class TestMutableCommentToFrozen:
    def test_to_frozen_type(self):
        c = MutableComment(comment_id=2, author="Alice")
        c.paragraphs.add_paragraph("Nice work")
        frozen = c._to_frozen()
        assert isinstance(frozen, Comment)

    def test_to_frozen_fields(self):
        c = MutableComment(
            comment_id=5,
            author="Bob",
            date="2024-01-15T10:00:00Z",
            initials="BB",
        )
        c.paragraphs.add_paragraph("Comment text")
        frozen = c._to_frozen()
        assert frozen.comment_id == 5
        assert frozen.author == "Bob"
        assert frozen.date == "2024-01-15T10:00:00Z"
        assert frozen.initials == "BB"
        assert len(frozen.paragraphs) == 1

    def test_to_frozen_paragraph_count(self):
        c = MutableComment(comment_id=1)
        c.paragraphs.add_paragraph("Para 1")
        c.paragraphs.add_paragraph("Para 2")
        frozen = c._to_frozen()
        assert len(frozen.paragraphs) == 2


class TestMutableCommentRef:
    def test_construction(self):
        ref = MutableCommentRef(comment_id=5)
        assert ref.comment_id == 5

    def test_get_text_empty(self):
        ref = MutableCommentRef(comment_id=1)
        assert ref.get_text() == ""

    def test_to_frozen(self):
        ref = MutableCommentRef(comment_id=3)
        frozen = ref._to_frozen()
        assert isinstance(frozen, CommentRef)
        assert frozen.comment_id == 3

    def test_repr(self):
        ref = MutableCommentRef(comment_id=7)
        assert "7" in repr(ref)


class TestDocumentAddComment:
    def test_add_comment_returns_mutable_comment(self):
        from docwow.api import DocumentWrapper
        doc = DocumentWrapper()
        c = doc.add_comment(author="Alice", text="Looks good")
        assert isinstance(c, MutableComment)
        assert c.author == "Alice"
        assert c.get_text() == "Looks good"

    def test_add_comment_sequential_ids(self):
        from docwow.api import DocumentWrapper
        doc = DocumentWrapper()
        c1 = doc.add_comment(text="First")
        c2 = doc.add_comment(text="Second")
        assert c1.comment_id == 1
        assert c2.comment_id == 2

    def test_add_comment_no_text(self):
        from docwow.api import DocumentWrapper
        doc = DocumentWrapper()
        c = doc.add_comment(author="Bob")
        assert c.get_text() == ""

    def test_comments_property(self):
        from docwow.api import DocumentWrapper
        doc = DocumentWrapper()
        doc.add_comment(text="A")
        doc.add_comment(text="B")
        assert len(doc.comments) == 2

    def test_add_comment_ref_in_run(self):
        from docwow.api import DocumentWrapper
        doc = DocumentWrapper()
        c = doc.add_comment(author="Alice", text="See here")
        para = doc.paragraphs.add_paragraph()
        para.runs.add_text("Some text")
        ref = para.runs.add_comment_ref(comment_id=c.comment_id)
        assert isinstance(ref, MutableCommentRef)
        assert ref.comment_id == 1


class TestCommentRoundTripDocx:
    def test_docx_round_trip(self):
        import io
        import zipfile
        import docwow
        from docwow.api import DocumentWrapper

        doc = DocumentWrapper()
        c = doc.add_comment(author="Alice", text="Good point!", date="2024-01-15T10:00:00Z", initials="A")
        para = doc.paragraphs.add_paragraph()
        para.runs.add_text("Important text")
        para.runs.add_comment_ref(comment_id=c.comment_id)

        docx_bytes = doc.to_bytes()

        with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
            assert "word/comments.xml" in zf.namelist()

        doc2 = docwow.open(docx_bytes)
        assert len(doc2.comments) == 1
        c2 = doc2.comments[0]
        assert c2.comment_id == 1
        assert c2.author == "Alice"
        assert c2.get_text() == "Good point!"
        assert c2.date == "2024-01-15T10:00:00Z"

        # Comment ref preserved in body
        from docwow.api.comment import MutableCommentRef
        body_para = doc2.paragraphs[0]
        refs = [r for r in body_para.runs if isinstance(r, MutableCommentRef)]
        assert len(refs) == 1
        assert refs[0].comment_id == 1

    def test_no_comments_no_xml_part(self):
        import io
        import zipfile
        from docwow.api import DocumentWrapper

        doc = DocumentWrapper()
        doc.paragraphs.add_paragraph("No comments here")
        docx_bytes = doc.to_bytes()

        with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
            assert "word/comments.xml" not in zf.namelist()
