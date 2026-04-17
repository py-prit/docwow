"""Mutable comment wrappers."""
from __future__ import annotations

from docwow.api.paragraph import ParagraphCollection
from docwow.models.comment import Comment


class MutableComment:
    """A mutable document comment (annotation).

    Access the comment text via :attr:`paragraphs`.  Use
    :meth:`set_author` and :meth:`set_date` to change metadata.
    """

    def __init__(
        self,
        comment_id: int,
        author: str = "",
        date: str = "",
        initials: str = "",
        paragraphs: ParagraphCollection | None = None,
    ) -> None:
        self._comment_id = comment_id
        self._author = author
        self._date = date
        self._initials = initials
        self._paragraphs = paragraphs if paragraphs is not None else ParagraphCollection()

    @property
    def comment_id(self) -> int:
        """The integer ID of this comment (matches the in-body reference marker)."""
        return self._comment_id

    @property
    def author(self) -> str:
        """Display name of the comment author."""
        return self._author

    @property
    def date(self) -> str:
        """ISO-8601 datetime string when the comment was made, or empty string."""
        return self._date

    @property
    def initials(self) -> str:
        """Author initials as stored in the DOCX."""
        return self._initials

    @property
    def paragraphs(self) -> ParagraphCollection:
        """Mutable paragraph collection for this comment's text content."""
        return self._paragraphs

    def set_author(self, author: str) -> "MutableComment":
        """Set the comment author display name."""
        self._author = author
        return self

    def set_date(self, date: str) -> "MutableComment":
        """Set the comment date (ISO-8601 string, e.g. ``"2024-01-15T10:30:00Z"``)."""
        self._date = date
        return self

    def set_initials(self, initials: str) -> "MutableComment":
        """Set the author initials."""
        self._initials = initials
        return self

    def get_text(self) -> str:
        """Return the concatenated text of all runs in all paragraphs."""
        from docwow.api.paragraph import MutableParagraph
        return "".join(
            item.get_text()
            for item in self._paragraphs
            if isinstance(item, MutableParagraph)
        )

    def _to_frozen(self) -> Comment:
        """Convert to a frozen Comment for pipeline use."""
        from docwow.models.paragraph import PageBreak
        frozen_paras = [
            item._to_frozen()
            for item in self._paragraphs
            if not isinstance(item, PageBreak)
        ]
        return Comment(
            comment_id=self._comment_id,
            author=self._author,
            date=self._date,
            initials=self._initials,
            paragraphs=tuple(frozen_paras),
        )

    def __repr__(self) -> str:
        return f"MutableComment(id={self._comment_id}, author={self._author!r})"


class MutableCommentRef:
    """A mutable inline comment reference marker.

    Place this inside a paragraph's :class:`~docwow.api.run.RunCollection`
    to mark where the comment superscript appears in the text.
    """

    def __init__(self, comment_id: int) -> None:
        self._comment_id = comment_id

    @property
    def comment_id(self) -> int:
        return self._comment_id

    def get_text(self) -> str:
        """Comment refs have no direct text content."""
        return ""

    def _to_frozen(self):
        from docwow.models.paragraph import CommentRef
        return CommentRef(comment_id=self._comment_id)

    def __repr__(self) -> str:
        return f"MutableCommentRef(id={self._comment_id})"
