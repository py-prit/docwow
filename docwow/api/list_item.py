"""Mutable list item wrapper."""

from __future__ import annotations

from docwow.models.lists import ListInfo
from docwow.models.paragraph import Paragraph
from docwow.models.styles import ParagraphFormatting
from docwow.api.run import RunCollection
from docwow.api.paragraph import MutableParagraph


class MutableListItem(MutableParagraph):
    """
    A paragraph that is a list item.

    Inherits all MutableParagraph methods and adds list-specific control
    over level and numbering definition ID.
    """

    def __init__(
        self,
        text: str = "",
        num_id: str = "1",
        level: int = 0,
        formatting: ParagraphFormatting | None = None,
    ) -> None:
        super().__init__(formatting=formatting)
        self._validate_level(level)
        self._num_id = num_id
        self._level = level
        if text:
            self.set_text(text)

    # ---- List-specific setters -----------------------------------------------

    def set_level(self, level: int) -> "MutableListItem":
        """Set the list nesting level (0–8)."""
        self._validate_level(level)
        self._level = level
        return self

    def set_num_id(self, num_id: str) -> "MutableListItem":
        """Set the numbering definition ID."""
        self._num_id = num_id
        return self

    # ---- Read-back -----------------------------------------------------------

    @property
    def level(self) -> int:
        return self._level

    @property
    def num_id(self) -> str:
        return self._num_id

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> Paragraph:
        """Convert to a frozen Paragraph with list_info populated."""
        return Paragraph(
            runs=self._runs._to_frozen(),
            formatting=self._fmt,
            list_info=ListInfo(num_id=self._num_id, level=self._level),
        )

    # ---- Validation ----------------------------------------------------------

    @staticmethod
    def _validate_level(level: int) -> None:
        if not isinstance(level, int) or not (0 <= level <= 8):
            raise ValueError(
                f"List level must be an integer between 0 and 8, got {level!r}"
            )

    def __repr__(self) -> str:
        return (
            f"MutableListItem({self.get_text()!r}, "
            f"level={self._level}, num_id={self._num_id!r})"
        )
