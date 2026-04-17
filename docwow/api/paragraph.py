"""Mutable paragraph wrapper and ParagraphCollection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from docwow.models.lists import ListInfo
from docwow.models.paragraph import PageBreak, Paragraph
from docwow.models.styles import ParagraphFormatting
from docwow.api.run import MutableImageRun, MutableRun, RunCollection

if TYPE_CHECKING:
    from docwow.api.table import MutableTable


class MutableParagraph:
    """A mutable paragraph containing an ordered sequence of runs."""

    def __init__(
        self,
        runs: RunCollection | None = None,
        formatting: ParagraphFormatting | None = None,
        list_info: ListInfo | None = None,
    ) -> None:
        self._runs = runs if runs is not None else RunCollection()
        self._fmt = formatting if formatting is not None else ParagraphFormatting()
        self._list_info = list_info

    # ---- Run access ----------------------------------------------------------

    @property
    def runs(self) -> RunCollection:
        """The collection of runs in this paragraph."""
        return self._runs

    # ---- Para-level formatting setters --------------------------------------

    def set_style(self, style_id: str | None) -> "MutableParagraph":
        """Set the paragraph style by style ID."""
        self._fmt = ParagraphFormatting(
            style_id=style_id,
            alignment=self._fmt.alignment,
            indent_left_pt=self._fmt.indent_left_pt,
            indent_right_pt=self._fmt.indent_right_pt,
            indent_first_line_pt=self._fmt.indent_first_line_pt,
            space_before_pt=self._fmt.space_before_pt,
            space_after_pt=self._fmt.space_after_pt,
            line_spacing_pt=self._fmt.line_spacing_pt,
            keep_together=self._fmt.keep_together,
            keep_with_next=self._fmt.keep_with_next,
            page_break_before=self._fmt.page_break_before,
            shading=self._fmt.shading,
        )
        return self

    def set_alignment(self, alignment: str | None) -> "MutableParagraph":
        """Set alignment: 'left', 'center', 'right', 'justify', or None."""
        if alignment not in ("left", "center", "right", "justify", None):
            raise ValueError(
                f"alignment must be 'left', 'center', 'right', 'justify', or None; "
                f"got {alignment!r}"
            )
        self._fmt = ParagraphFormatting(
            style_id=self._fmt.style_id,
            alignment=alignment,
            indent_left_pt=self._fmt.indent_left_pt,
            indent_right_pt=self._fmt.indent_right_pt,
            indent_first_line_pt=self._fmt.indent_first_line_pt,
            space_before_pt=self._fmt.space_before_pt,
            space_after_pt=self._fmt.space_after_pt,
            line_spacing_pt=self._fmt.line_spacing_pt,
            keep_together=self._fmt.keep_together,
            keep_with_next=self._fmt.keep_with_next,
            page_break_before=self._fmt.page_break_before,
            shading=self._fmt.shading,
        )
        return self

    def set_indent(
        self,
        left_pt: float = 0.0,
        right_pt: float = 0.0,
        first_line_pt: float = 0.0,
    ) -> "MutableParagraph":
        """Set paragraph indentation in points."""
        self._fmt = ParagraphFormatting(
            style_id=self._fmt.style_id,
            alignment=self._fmt.alignment,
            indent_left_pt=left_pt,
            indent_right_pt=right_pt,
            indent_first_line_pt=first_line_pt,
            space_before_pt=self._fmt.space_before_pt,
            space_after_pt=self._fmt.space_after_pt,
            line_spacing_pt=self._fmt.line_spacing_pt,
            keep_together=self._fmt.keep_together,
            keep_with_next=self._fmt.keep_with_next,
            page_break_before=self._fmt.page_break_before,
            shading=self._fmt.shading,
        )
        return self

    def set_spacing(
        self,
        before_pt: float = 0.0,
        after_pt: float = 0.0,
        line_pt: float | None = None,
    ) -> "MutableParagraph":
        """Set paragraph spacing in points."""
        self._fmt = ParagraphFormatting(
            style_id=self._fmt.style_id,
            alignment=self._fmt.alignment,
            indent_left_pt=self._fmt.indent_left_pt,
            indent_right_pt=self._fmt.indent_right_pt,
            indent_first_line_pt=self._fmt.indent_first_line_pt,
            space_before_pt=before_pt,
            space_after_pt=after_pt,
            line_spacing_pt=line_pt,
            keep_together=self._fmt.keep_together,
            keep_with_next=self._fmt.keep_with_next,
            page_break_before=self._fmt.page_break_before,
            shading=self._fmt.shading,
        )
        return self

    def set_keep_together(self, value: bool = True) -> "MutableParagraph":
        """Keep paragraph lines together across page breaks."""
        self._fmt = ParagraphFormatting(
            style_id=self._fmt.style_id,
            alignment=self._fmt.alignment,
            indent_left_pt=self._fmt.indent_left_pt,
            indent_right_pt=self._fmt.indent_right_pt,
            indent_first_line_pt=self._fmt.indent_first_line_pt,
            space_before_pt=self._fmt.space_before_pt,
            space_after_pt=self._fmt.space_after_pt,
            line_spacing_pt=self._fmt.line_spacing_pt,
            keep_together=value,
            keep_with_next=self._fmt.keep_with_next,
            page_break_before=self._fmt.page_break_before,
            shading=self._fmt.shading,
        )
        return self

    def set_keep_with_next(self, value: bool = True) -> "MutableParagraph":
        """Keep this paragraph on the same page as the following paragraph."""
        self._fmt = ParagraphFormatting(
            style_id=self._fmt.style_id,
            alignment=self._fmt.alignment,
            indent_left_pt=self._fmt.indent_left_pt,
            indent_right_pt=self._fmt.indent_right_pt,
            indent_first_line_pt=self._fmt.indent_first_line_pt,
            space_before_pt=self._fmt.space_before_pt,
            space_after_pt=self._fmt.space_after_pt,
            line_spacing_pt=self._fmt.line_spacing_pt,
            keep_together=self._fmt.keep_together,
            keep_with_next=value,
            page_break_before=self._fmt.page_break_before,
            shading=self._fmt.shading,
        )
        return self

    def set_page_break_before(self, value: bool = True) -> "MutableParagraph":
        """Force a page break before this paragraph."""
        self._fmt = ParagraphFormatting(
            style_id=self._fmt.style_id,
            alignment=self._fmt.alignment,
            indent_left_pt=self._fmt.indent_left_pt,
            indent_right_pt=self._fmt.indent_right_pt,
            indent_first_line_pt=self._fmt.indent_first_line_pt,
            space_before_pt=self._fmt.space_before_pt,
            space_after_pt=self._fmt.space_after_pt,
            line_spacing_pt=self._fmt.line_spacing_pt,
            keep_together=self._fmt.keep_together,
            keep_with_next=self._fmt.keep_with_next,
            page_break_before=value,
            shading=self._fmt.shading,
        )
        return self

    # ---- Para-level convenience (loops over all runs) ------------------------

    def get_text(self) -> str:
        """Return the concatenated text of all runs."""
        return "".join(
            r.get_text() for r in self._runs if isinstance(r, MutableRun)
        )

    def set_text(self, text: str) -> "MutableParagraph":
        """Replace all runs with a single run containing the given text."""
        self._runs.clear()
        self._runs.add_text(text)
        return self

    def set_bold(self, value: bool = True) -> "MutableParagraph":
        """Set bold on all text runs."""
        for run in self._runs:
            if isinstance(run, MutableRun):
                run.set_bold(value)
        return self

    def set_italic(self, value: bool = True) -> "MutableParagraph":
        """Set italic on all text runs."""
        for run in self._runs:
            if isinstance(run, MutableRun):
                run.set_italic(value)
        return self

    def set_underline(self, value: bool = True) -> "MutableParagraph":
        """Set underline on all text runs."""
        for run in self._runs:
            if isinstance(run, MutableRun):
                run.set_underline(value)
        return self

    def set_font_name(self, name: str | None) -> "MutableParagraph":
        """Set font name on all text runs."""
        for run in self._runs:
            if isinstance(run, MutableRun):
                run.set_font_name(name)
        return self

    def set_font_size(self, pt: float | None) -> "MutableParagraph":
        """Set font size (in points) on all text runs."""
        for run in self._runs:
            if isinstance(run, MutableRun):
                run.set_font_size(pt)
        return self

    def set_color(self, hex_rgb: str | None) -> "MutableParagraph":
        """Set text color (hex RGB) on all text runs."""
        for run in self._runs:
            if isinstance(run, MutableRun):
                run.set_color(hex_rgb)
        return self

    # ---- Formatting read-back -----------------------------------------------

    @property
    def style_id(self) -> str | None:
        """Named Word style ID (e.g. ``'Heading1'``, ``'Normal'``)."""
        return self._fmt.style_id

    @property
    def alignment(self) -> str | None:
        """Text alignment: ``'left'``, ``'center'``, ``'right'``, ``'justify'``, or ``None``."""
        return self._fmt.alignment

    @property
    def indent_left_pt(self) -> float:
        """Left indent in points."""
        return self._fmt.indent_left_pt

    @property
    def indent_right_pt(self) -> float:
        """Right indent in points."""
        return self._fmt.indent_right_pt

    @property
    def indent_first_line_pt(self) -> float:
        """First-line indent in points (negative = hanging indent)."""
        return self._fmt.indent_first_line_pt

    @property
    def space_before_pt(self) -> float:
        """Space before the paragraph in points."""
        return self._fmt.space_before_pt

    @property
    def space_after_pt(self) -> float:
        """Space after the paragraph in points."""
        return self._fmt.space_after_pt

    @property
    def line_spacing_pt(self) -> float | None:
        """Exact line spacing in points, or ``None`` for automatic."""
        return self._fmt.line_spacing_pt

    @property
    def keep_together(self) -> bool:
        """Whether all lines of this paragraph are kept on the same page."""
        return self._fmt.keep_together

    @property
    def keep_with_next(self) -> bool:
        """Whether this paragraph is kept on the same page as the following one."""
        return self._fmt.keep_with_next

    @property
    def page_break_before(self) -> bool:
        """Whether a page break is forced before this paragraph."""
        return self._fmt.page_break_before

    @property
    def shading(self) -> str | None:
        """Background shading color as a 6-digit hex RGB string (e.g. ``'4472C4'``), or ``None``."""
        return self._fmt.shading

    def set_shading(self, hex_rgb: str | None) -> "MutableParagraph":
        """Set the paragraph background shading color (6-digit hex RGB, e.g. ``'4472C4'``) or ``None`` to clear."""
        self._fmt = ParagraphFormatting(
            style_id=self._fmt.style_id,
            alignment=self._fmt.alignment,
            indent_left_pt=self._fmt.indent_left_pt,
            indent_right_pt=self._fmt.indent_right_pt,
            indent_first_line_pt=self._fmt.indent_first_line_pt,
            space_before_pt=self._fmt.space_before_pt,
            space_after_pt=self._fmt.space_after_pt,
            line_spacing_pt=self._fmt.line_spacing_pt,
            keep_together=self._fmt.keep_together,
            keep_with_next=self._fmt.keep_with_next,
            page_break_before=self._fmt.page_break_before,
            shading=hex_rgb.upper() if hex_rgb else None,
        )
        return self

    # ---- List info (internal use; MutableListItem provides nicer surface) ----

    @property
    def list_info(self) -> ListInfo | None:
        """List metadata if this paragraph is a list item, else None."""
        return self._list_info

    def _set_list_info(self, info: ListInfo | None) -> None:
        self._list_info = info

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> Paragraph:
        """Convert to a frozen Paragraph for pipeline use."""
        return Paragraph(
            runs=self._runs._to_frozen(),
            formatting=self._fmt,
            list_info=self._list_info,
        )

    def __repr__(self) -> str:
        return (
            f"MutableParagraph(runs={len(self._runs)}, "
            f"style={self._fmt.style_id!r}, "
            f"alignment={self._fmt.alignment!r})"
        )


class ParagraphCollection:
    """Ordered mutable collection of body elements (paragraphs, list items, images, tables)."""

    def __init__(self) -> None:
        self._items: list[MutableParagraph | "MutableTable"] = []

    # ---- Sequence protocol ---------------------------------------------------

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[MutableParagraph | "MutableTable"]:
        return iter(self._items)

    def __getitem__(self, index: int) -> MutableParagraph | "MutableTable":
        return self._items[index]

    # ---- Mutation ------------------------------------------------------------

    def append(self, item: "MutableParagraph | MutableTable") -> None:
        """Append a paragraph or table to the collection."""
        self._check_type(item)
        self._items.append(item)

    def insert(self, index: int, item: "MutableParagraph | MutableTable") -> None:
        """Insert a paragraph or table at the given index."""
        self._check_type(item)
        self._items.insert(index, item)

    def remove(self, index: int) -> None:
        """Remove the item at the given index."""
        del self._items[index]

    def clear(self) -> None:
        """Remove all items."""
        self._items.clear()

    # ---- Convenience factories -----------------------------------------------

    def add_paragraph(
        self, text: str = "", style_id: str | None = None
    ) -> MutableParagraph:
        """Create and append a new paragraph, returning it."""
        fmt = ParagraphFormatting(style_id=style_id)
        para = MutableParagraph(formatting=fmt)
        if text:
            para.set_text(text)
        self._items.append(para)
        return para

    def add_list_item(
        self, text: str = "", level: int = 0, num_id: str = "1"
    ) -> "MutableListItem":
        """Create and append a new list item, returning it."""
        from docwow.api.list_item import MutableListItem
        item = MutableListItem(text=text, num_id=num_id, level=level)
        self._items.append(item)
        return item

    def add_page_break(self) -> PageBreak:
        """Append an explicit page break and return it."""
        pb = PageBreak()
        self._items.append(pb)
        return pb

    def add_image(
        self,
        data: bytes,
        content_type: str,
        width_pt: float,
        height_pt: float,
        alt_text: str = "",
    ) -> "MutableImage":
        """Create and append a new image paragraph, returning it."""
        from docwow.api.image import MutableImage
        img = MutableImage(
            data=data,
            content_type=content_type,
            width_pt=width_pt,
            height_pt=height_pt,
            alt_text=alt_text,
        )
        self._items.append(img)
        return img

    def add_table(
        self,
        rows: int,
        cols: int,
        width_pt: float | None = None,
        style_id: str | None = None,
    ) -> "MutableTable":
        """Create and append a new table with *rows* × *cols* empty cells, returning it.

        Args:
            rows: Number of rows.
            cols: Number of columns (cells per row).
            width_pt: Optional total table width in points.
            style_id: Optional Word table style ID (e.g. ``'TableGrid'``).
        """
        from docwow.api.table import MutableTable, MutableTableRow, MutableTableCell
        table_rows = [
            MutableTableRow(cells=[MutableTableCell() for _ in range(cols)])
            for _ in range(rows)
        ]
        table = MutableTable(rows=table_rows, width_pt=width_pt, style_id=style_id)
        self._items.append(table)
        return table

    def add_toc(
        self,
        title: str = "Contents",
    ) -> "MutableTableOfContents":
        """Create and append a new Table of Contents, returning it.

        Args:
            title: Heading text shown above the TOC list.  Defaults to
                   ``"Contents"``.
        """
        from docwow.api.toc import MutableTableOfContents
        toc = MutableTableOfContents(title=title)
        self._items.append(toc)
        return toc

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen_body(self) -> tuple:
        """Convert all items to frozen body elements."""
        from docwow.api.toc import MutableTableOfContents
        result = []
        for item in self._items:
            if isinstance(item, PageBreak):
                result.append(item)  # already frozen
            else:
                result.append(item._to_frozen())
        return tuple(result)

    # ---- Type enforcement ----------------------------------------------------

    def _check_type(self, item: object) -> None:
        from docwow.api.table import MutableTable as MT
        from docwow.api.toc import MutableTableOfContents as MTOC
        if not isinstance(item, (MutableParagraph, MT, PageBreak, MTOC)):
            if isinstance(item, Paragraph):
                raise TypeError(
                    "Cannot add a frozen Paragraph directly. "
                    "Use MutableParagraph or call paragraphs.add_paragraph() instead."
                )
            raise TypeError(
                f"Expected MutableParagraph, MutableTable, MutableTableOfContents, "
                f"or PageBreak; got {type(item).__name__!r}"
            )

    def __repr__(self) -> str:
        return f"ParagraphCollection({len(self._items)} items)"


# Avoid circular import — MutableListItem is a subclass of MutableParagraph
from docwow.api.list_item import MutableListItem  # noqa: E402
from docwow.api.image import MutableImage  # noqa: E402
