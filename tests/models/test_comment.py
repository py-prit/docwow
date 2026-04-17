"""Tests for docwow.models.comment — Comment model."""
from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.comment import Comment
from docwow.models.paragraph import CommentRef, Paragraph


class TestCommentConstruction:
    def test_required_fields(self):
        c = Comment(comment_id=1, author="Alice", paragraphs=())
        assert c.comment_id == 1
        assert c.author == "Alice"
        assert c.paragraphs == ()
        assert c.date == ""
        assert c.initials == ""

    def test_all_fields(self):
        para = Paragraph(runs=())
        c = Comment(
            comment_id=3,
            author="Bob",
            date="2024-01-15T10:30:00Z",
            initials="BB",
            paragraphs=(para,),
        )
        assert c.comment_id == 3
        assert c.author == "Bob"
        assert c.date == "2024-01-15T10:30:00Z"
        assert c.initials == "BB"
        assert len(c.paragraphs) == 1


class TestCommentImmutability:
    def test_frozen(self):
        c = Comment(comment_id=1, author="Alice", paragraphs=())
        with pytest.raises(FrozenInstanceError):
            c.author = "Bob"  # type: ignore[misc]


class TestCommentEquality:
    def test_equal(self):
        c1 = Comment(comment_id=1, author="Alice", paragraphs=())
        c2 = Comment(comment_id=1, author="Alice", paragraphs=())
        assert c1 == c2

    def test_not_equal_id(self):
        assert Comment(comment_id=1, author="A", paragraphs=()) != Comment(comment_id=2, author="A", paragraphs=())

    def test_not_equal_author(self):
        assert Comment(comment_id=1, author="A", paragraphs=()) != Comment(comment_id=1, author="B", paragraphs=())


class TestCommentRefModel:
    def test_construction(self):
        ref = CommentRef(comment_id=5)
        assert ref.comment_id == 5

    def test_frozen(self):
        ref = CommentRef(comment_id=1)
        with pytest.raises(FrozenInstanceError):
            ref.comment_id = 2  # type: ignore[misc]

    def test_equality(self):
        assert CommentRef(comment_id=1) == CommentRef(comment_id=1)
        assert CommentRef(comment_id=1) != CommentRef(comment_id=2)
