"""Mutable footnote and endnote wrappers."""
from __future__ import annotations

from docwow.api.paragraph import ParagraphCollection
from docwow.models.footnote import Footnote


class MutableFootnote:
    """A mutable footnote or endnote body.

    Access the note body content via :attr:`paragraphs`.
    """

    def __init__(
        self,
        note_id: int,
        paragraphs: ParagraphCollection | None = None,
        note_type: str = "footnote",
    ) -> None:
        self._note_id = note_id
        self._paragraphs = paragraphs if paragraphs is not None else ParagraphCollection()
        self._note_type = note_type

    @property
    def note_id(self) -> int:
        """The integer ID of this note (matches the in-body reference marker)."""
        return self._note_id

    @property
    def note_type(self) -> str:
        """``'footnote'`` or ``'endnote'``."""
        return self._note_type

    @property
    def paragraphs(self) -> ParagraphCollection:
        """The mutable paragraph collection for this note's content."""
        return self._paragraphs

    def get_text(self) -> str:
        """Return the concatenated text of all runs in all paragraphs."""
        from docwow.api.paragraph import MutableParagraph
        return "".join(
            item.get_text()
            for item in self._paragraphs
            if isinstance(item, MutableParagraph)
        )

    def _to_frozen(self) -> Footnote:
        """Convert to a frozen Footnote for pipeline use."""
        from docwow.models.paragraph import PageBreak
        frozen_paras = [
            item._to_frozen()
            for item in self._paragraphs
            if not isinstance(item, PageBreak)
        ]
        return Footnote(
            note_id=self._note_id,
            paragraphs=tuple(frozen_paras),
            note_type=self._note_type,
        )

    def __repr__(self) -> str:
        return f"MutableFootnote(id={self._note_id}, type={self._note_type!r})"


class MutableFootnoteRef:
    """A mutable inline footnote or endnote reference marker.

    This is placed inside a paragraph's :class:`~docwow.api.run.RunCollection`
    to mark where the superscript reference appears in the text.
    """

    def __init__(self, note_id: int, note_type: str = "footnote") -> None:
        self._note_id = note_id
        self._note_type = note_type

    @property
    def note_id(self) -> int:
        """The integer ID of this reference (matches the note body's ``note_id``)."""
        return self._note_id

    @property
    def note_type(self) -> str:
        """``'footnote'`` or ``'endnote'``."""
        return self._note_type

    def get_text(self) -> str:
        """Footnote refs have no direct text content."""
        return ""

    def _to_frozen(self):
        from docwow.models.paragraph import FootnoteRef
        return FootnoteRef(note_id=self._note_id, note_type=self._note_type)

    def __repr__(self) -> str:
        return f"MutableFootnoteRef(id={self._note_id}, type={self._note_type!r})"
