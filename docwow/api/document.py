"""Top-level mutable document wrapper."""

from __future__ import annotations

from pathlib import Path

from docwow.models.lists import NumberingDefinition
from docwow.models.styles import Style
from docwow.api.paragraph import ParagraphCollection


class DocumentWrapper:
    """
    Mutable document object returned by ``docwow.open()``.

    All document content is accessible and editable through this object.
    Call :meth:`save` or :meth:`to_bytes` to produce a DOCX file.
    Call :meth:`to_html` to produce an HTML string.
    """

    def __init__(
        self,
        paragraphs: ParagraphCollection | None = None,
        styles: tuple[Style, ...] = (),
        numbering: tuple[NumberingDefinition, ...] = (),
        page_width_pt: float = 595.28,
        page_height_pt: float = 841.89,
        margin_top_pt: float = 72.0,
        margin_bottom_pt: float = 72.0,
        margin_left_pt: float = 72.0,
        margin_right_pt: float = 72.0,
    ) -> None:
        self._paragraphs = paragraphs if paragraphs is not None else ParagraphCollection()
        self._styles = styles
        self._numbering = numbering
        self._page_width_pt = page_width_pt
        self._page_height_pt = page_height_pt
        self._margin_top_pt = margin_top_pt
        self._margin_bottom_pt = margin_bottom_pt
        self._margin_left_pt = margin_left_pt
        self._margin_right_pt = margin_right_pt

    # ---- Body access ---------------------------------------------------------

    @property
    def paragraphs(self) -> ParagraphCollection:
        """The collection of body elements (paragraphs, lists, images, tables)."""
        return self._paragraphs

    # ---- Page geometry -------------------------------------------------------

    def set_page_size(self, width_pt: float, height_pt: float) -> "DocumentWrapper":
        """Set the page dimensions in points."""
        self._page_width_pt = width_pt
        self._page_height_pt = height_pt
        return self

    def set_margins(
        self,
        top_pt: float = 72.0,
        bottom_pt: float = 72.0,
        left_pt: float = 72.0,
        right_pt: float = 72.0,
    ) -> "DocumentWrapper":
        """Set all page margins in points."""
        self._margin_top_pt = top_pt
        self._margin_bottom_pt = bottom_pt
        self._margin_left_pt = left_pt
        self._margin_right_pt = right_pt
        return self

    @property
    def page_width_pt(self) -> float:
        return self._page_width_pt

    @property
    def page_height_pt(self) -> float:
        return self._page_height_pt

    @property
    def margin_top_pt(self) -> float:
        return self._margin_top_pt

    @property
    def margin_bottom_pt(self) -> float:
        return self._margin_bottom_pt

    @property
    def margin_left_pt(self) -> float:
        return self._margin_left_pt

    @property
    def margin_right_pt(self) -> float:
        return self._margin_right_pt

    # ---- Numbering -----------------------------------------------------------

    def add_numbering_definition(self, num_fmt: str = "bullet") -> str:
        """
        Register a new numbering definition and return its ``num_id``.

        Use the returned ``num_id`` when calling
        ``doc.paragraphs.add_list_item(num_id=...)``.

        Args:
            num_fmt: List format for all levels — ``'bullet'``, ``'decimal'``,
                     ``'lowerLetter'``, ``'upperLetter'``, ``'lowerRoman'``,
                     ``'upperRoman'``.

        Returns:
            The new ``num_id`` string.
        """
        from docwow.models.lists import ListLevel

        new_num_id = str(len(self._numbering) + 1)
        abstract_num_id = f"abs_{new_num_id}"

        levels = tuple(
            ListLevel(
                level=i,
                num_fmt=num_fmt,
                start_value=1,
                text_template=f"%{i + 1}.",
                indent_pt=360.0 * (i + 1),
                hanging_pt=360.0,
            )
            for i in range(9)
        )

        new_def = NumberingDefinition(
            abstract_num_id=abstract_num_id,
            levels=levels,
        )
        self._numbering = self._numbering + (new_def,)
        return new_num_id

    # ---- Output --------------------------------------------------------------

    def _to_frozen(self):
        """Convert the wrapper tree to a frozen Document."""
        from docwow.api._convert import document_to_frozen
        return document_to_frozen(self)

    def to_bytes(self) -> bytes:
        """Serialise the document to DOCX bytes."""
        from docwow.writer.docx_writer import write_docx
        return write_docx(self._to_frozen())

    def save(self, path: str | Path) -> None:
        """Write the document to a DOCX file at the given path."""
        data = self.to_bytes()
        Path(path).write_bytes(data)

    def to_html(self) -> str:
        """Render the document to an HTML string."""
        from docwow.renderer.html_renderer import render_document
        return render_document(self._to_frozen())

    def __repr__(self) -> str:
        return (
            f"DocumentWrapper(paragraphs={len(self._paragraphs)}, "
            f"page={self._page_width_pt:.1f}x{self._page_height_pt:.1f}pt)"
        )
