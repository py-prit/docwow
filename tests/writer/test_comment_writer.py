"""Tests for docwow.writer.comment_writer."""
from __future__ import annotations

from lxml import etree

from docwow.models.comment import Comment
from docwow.models.paragraph import Paragraph, TextRun
from docwow.writer.comment_writer import write_comments


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _parse(xml_bytes: bytes):
    return etree.fromstring(xml_bytes)


def _para(text: str) -> Paragraph:
    return Paragraph(runs=(TextRun(text=text),))


class TestWriteCommentsEmpty:
    def test_produces_comments_root(self):
        xml = write_comments(())
        root = _parse(xml)
        assert root.tag == f"{{{W}}}comments"
        assert len(root) == 0


class TestWriteCommentsSingle:
    def _root(self):
        c = Comment(
            comment_id=1,
            author="Alice",
            date="2024-01-15T10:00:00Z",
            initials="A",
            paragraphs=(_para("Fix this."),),
        )
        return _parse(write_comments((c,)))

    def test_comment_element(self):
        root = self._root()
        assert len(root) == 1
        assert root[0].tag == f"{{{W}}}comment"

    def test_comment_id_attr(self):
        root = self._root()
        assert root[0].get(f"{{{W}}}id") == "1"

    def test_author_attr(self):
        root = self._root()
        assert root[0].get(f"{{{W}}}author") == "Alice"

    def test_date_attr(self):
        root = self._root()
        assert root[0].get(f"{{{W}}}date") == "2024-01-15T10:00:00Z"

    def test_initials_attr(self):
        root = self._root()
        assert root[0].get(f"{{{W}}}initials") == "A"

    def test_paragraph_written(self):
        root = self._root()
        comment_el = root[0]
        paras = [c for c in comment_el if c.tag == f"{{{W}}}p"]
        assert len(paras) == 1

    def test_comment_text_style(self):
        root = self._root()
        comment_el = root[0]
        ppr = comment_el[0].find(f"{{{W}}}pPr")
        pstyle = ppr.find(f"{{{W}}}pStyle")
        assert pstyle.get(f"{{{W}}}val") == "CommentText"

    def test_annotation_ref_marker(self):
        root = self._root()
        comment_el = root[0]
        p_el = comment_el[0]
        # First run should be the annotation ref marker
        runs = [c for c in p_el if c.tag == f"{{{W}}}r"]
        assert runs
        first_run = runs[0]
        assert first_run.find(f"{{{W}}}annotationRef") is not None


class TestWriteCommentsNoDateOrInitials:
    def test_missing_date_not_written(self):
        c = Comment(comment_id=1, author="Bob", paragraphs=(_para("x"),))
        root = _parse(write_comments((c,)))
        comment_el = root[0]
        assert comment_el.get(f"{{{W}}}date") is None

    def test_missing_initials_not_written(self):
        c = Comment(comment_id=1, author="Bob", paragraphs=(_para("x"),))
        root = _parse(write_comments((c,)))
        comment_el = root[0]
        assert comment_el.get(f"{{{W}}}initials") is None


class TestWriteMultipleComments:
    def test_two_comments(self):
        comments = (
            Comment(comment_id=1, author="Alice", paragraphs=(_para("First"),)),
            Comment(comment_id=2, author="Bob", paragraphs=(_para("Second"),)),
        )
        root = _parse(write_comments(comments))
        assert len(root) == 2
        assert root[0].get(f"{{{W}}}id") == "1"
        assert root[1].get(f"{{{W}}}id") == "2"


class TestCommentRefInDocumentXml:
    """Test that _write_comment_ref emits the correct OOXML sequence."""

    def test_comment_ref_writes_range_and_reference(self):
        from lxml import etree
        from docwow.models.paragraph import CommentRef, TextRun
        from docwow.writer.document_writer import _write_run

        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        parent = etree.Element(f"{{{W}}}p")
        run = CommentRef(comment_id=7)
        _write_run(parent, run, {}, [1], None)

        tags = [child.tag for child in parent]
        assert f"{{{W}}}commentRangeStart" in tags
        assert f"{{{W}}}commentRangeEnd" in tags
        assert f"{{{W}}}r" in tags

    def test_comment_range_start_id(self):
        from lxml import etree
        from docwow.models.paragraph import CommentRef
        from docwow.writer.document_writer import _write_run

        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        parent = etree.Element(f"{{{W}}}p")
        _write_run(parent, CommentRef(comment_id=4), {}, [1], None)

        start = parent.find(f"{{{W}}}commentRangeStart")
        assert start.get(f"{{{W}}}id") == "4"
        end = parent.find(f"{{{W}}}commentRangeEnd")
        assert end.get(f"{{{W}}}id") == "4"
