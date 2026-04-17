from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Comment:
    """A single document comment (annotation).

    ``comment_id`` matches the ``w:id`` attribute on the comment element and
    the ``comment_id`` of every :class:`~docwow.models.paragraph.CommentRef`
    that references it.

    ``author``   is the display name of the comment author.
    ``date``     is an ISO-8601 datetime string (``"2024-01-15T10:30:00Z"``),
                 or empty string when not present.
    ``initials`` is the author's initials as stored in the DOCX.

    ``paragraphs`` holds the comment text (usually one paragraph, but Word
    allows multiple).
    """

    comment_id: int
    author: str
    paragraphs: tuple  # tuple[Paragraph, ...] — avoids circular import
    date: str = ""
    initials: str = ""
