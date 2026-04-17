"""Top-level mutable document wrapper."""

from __future__ import annotations

from pathlib import Path

from docwow.models.lists import NumberingDefinition
from docwow.models.styles import Style
from docwow.api.comment import MutableComment
from docwow.api.footnote import MutableFootnote
from docwow.api.paragraph import ParagraphCollection
from docwow.api.header_footer import MutableHeaderFooter


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
        header_default: MutableHeaderFooter | None = None,
        header_first: MutableHeaderFooter | None = None,
        header_even: MutableHeaderFooter | None = None,
        footer_default: MutableHeaderFooter | None = None,
        footer_first: MutableHeaderFooter | None = None,
        footer_even: MutableHeaderFooter | None = None,
        title_pg: bool = False,
        footnotes: list[MutableFootnote] | None = None,
        endnotes: list[MutableFootnote] | None = None,
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
        self._header_default = header_default
        self._header_first = header_first
        self._header_even = header_even
        self._footer_default = footer_default
        self._footer_first = footer_first
        self._footer_even = footer_even
        self._title_pg = title_pg
        self._footnotes: list[MutableFootnote] = list(footnotes) if footnotes else []
        self._endnotes: list[MutableFootnote] = list(endnotes) if endnotes else []
        self._comments: list[MutableComment] = []

    # ---- Body access ---------------------------------------------------------

    @property
    def paragraphs(self) -> ParagraphCollection:
        """The collection of body elements (paragraphs, lists, images, tables)."""
        return self._paragraphs

    # ---- Headers / footers ---------------------------------------------------

    def _get_or_create_hf(self, attr: str) -> MutableHeaderFooter:
        if getattr(self, attr) is None:
            setattr(self, attr, MutableHeaderFooter())
        return getattr(self, attr)

    @property
    def header(self) -> MutableHeaderFooter:
        """The default-page header (created on first access if absent)."""
        if self._header_default is None:
            self._header_default = MutableHeaderFooter()
        return self._header_default

    @header.setter
    def header(self, value: MutableHeaderFooter | None) -> None:
        self._header_default = value

    @property
    def header_first(self) -> MutableHeaderFooter | None:
        """The first-page header (None if not set)."""
        return self._header_first

    @header_first.setter
    def header_first(self, value: MutableHeaderFooter | None) -> None:
        self._header_first = value

    @property
    def header_even(self) -> MutableHeaderFooter | None:
        """The even-page header (None if not set)."""
        return self._header_even

    @header_even.setter
    def header_even(self, value: MutableHeaderFooter | None) -> None:
        self._header_even = value

    @property
    def footer(self) -> MutableHeaderFooter:
        """The default-page footer (created on first access if absent)."""
        if self._footer_default is None:
            self._footer_default = MutableHeaderFooter()
        return self._footer_default

    @footer.setter
    def footer(self, value: MutableHeaderFooter | None) -> None:
        self._footer_default = value

    @property
    def footer_first(self) -> MutableHeaderFooter | None:
        """The first-page footer (None if not set)."""
        return self._footer_first

    @footer_first.setter
    def footer_first(self, value: MutableHeaderFooter | None) -> None:
        self._footer_first = value

    @property
    def footer_even(self) -> MutableHeaderFooter | None:
        """The even-page footer (None if not set)."""
        return self._footer_even

    @footer_even.setter
    def footer_even(self, value: MutableHeaderFooter | None) -> None:
        self._footer_even = value

    @property
    def title_pg(self) -> bool:
        """Whether the first page uses a different header/footer."""
        return self._title_pg

    @title_pg.setter
    def title_pg(self, value: bool) -> None:
        self._title_pg = value

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

    # ---- Footnotes / endnotes ------------------------------------------------

    @property
    def footnotes(self) -> list[MutableFootnote]:
        """All footnote bodies in the document."""
        return self._footnotes

    @property
    def endnotes(self) -> list[MutableFootnote]:
        """All endnote bodies in the document."""
        return self._endnotes

    # ---- Comments ------------------------------------------------------------

    @property
    def comments(self) -> list[MutableComment]:
        """All comment bodies in the document."""
        return self._comments

    def add_comment(
        self,
        author: str = "",
        text: str = "",
        date: str = "",
        initials: str = "",
    ) -> MutableComment:
        """Create a new comment body, register it, and return it.

        The returned :class:`~docwow.api.comment.MutableComment` has an
        auto-assigned sequential ``comment_id``. The optional *text* argument
        adds an initial paragraph with that content. Add a matching
        :meth:`~docwow.api.run.RunCollection.add_comment_ref` to the body
        paragraph where the superscript marker should appear.

        Args:
            author:   Display name of the comment author.
            text:     Initial comment text (creates one paragraph if non-empty).
            date:     ISO-8601 datetime string, e.g. ``"2024-01-15T10:30:00Z"``.
            initials: Author initials.
        """
        comment_id = len(self._comments) + 1
        comment = MutableComment(
            comment_id=comment_id,
            author=author,
            date=date,
            initials=initials,
        )
        if text:
            comment.paragraphs.add_paragraph(text)
        self._comments.append(comment)
        return comment

    @property
    def _comments_frozen(self):
        return tuple(c._to_frozen() for c in self._comments)

    # ---- Footnotes / endnotes ------------------------------------------------

    def add_footnote(self, note_type: str = "footnote") -> MutableFootnote:
        """Create a new footnote (or endnote) body, register it, and return it.

        The returned :class:`~docwow.api.footnote.MutableFootnote` has an
        auto-assigned sequential ``note_id``. Add content via its
        ``paragraphs`` collection, then add a matching
        :meth:`~docwow.api.run.RunCollection.add_footnote_ref` to the
        body paragraph where the marker should appear.

        Args:
            note_type: ``'footnote'`` (default) or ``'endnote'``.
        """
        lst = self._footnotes if note_type == "footnote" else self._endnotes
        note_id = len(lst) + 1
        note = MutableFootnote(note_id=note_id, note_type=note_type)
        lst.append(note)
        return note

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

    @property
    def _footnotes_frozen(self):
        return tuple(n._to_frozen() for n in self._footnotes)

    @property
    def _endnotes_frozen(self):
        return tuple(n._to_frozen() for n in self._endnotes)

    @property
    def _comments_frozen(self):
        return tuple(c._to_frozen() for c in self._comments)

    def to_bytes(self) -> bytes:
        """Serialise the document to DOCX bytes."""
        from docwow.writer.docx_writer import write_docx
        return write_docx(self._to_frozen())

    def save(self, path: str | Path) -> None:
        """Write the document to a DOCX file at the given path."""
        data = self.to_bytes()
        Path(path).write_bytes(data)

    def to_html(self, page_view: bool = False) -> str:
        """Render the document to an HTML string.

        Args:
            page_view: When True, styles the output as a physical page and
                       adds ``@media print`` / ``@page`` rules for correct
                       browser printing and PDF export.
        """
        from docwow.renderer.html_renderer import render_document
        return render_document(self._to_frozen(), page_view=page_view)

    def __repr__(self) -> str:
        return (
            f"DocumentWrapper(paragraphs={len(self._paragraphs)}, "
            f"page={self._page_width_pt:.1f}x{self._page_height_pt:.1f}pt)"
        )
