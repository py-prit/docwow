from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Footnote:
    """A single footnote or endnote body.

    ``note_id`` matches the ``w:id`` attribute in OOXML and the
    ``note_id`` of the :class:`~docwow.models.paragraph.FootnoteRef`
    that references it.

    ``note_type`` is either ``"footnote"`` or ``"endnote"``.

    ``paragraphs`` holds the full content of the note (usually one
    paragraph, but Word allows multiple).
    """

    note_id: int
    paragraphs: tuple  # tuple[Paragraph, ...] — avoids circular import
    note_type: str = "footnote"
