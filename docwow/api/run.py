"""Mutable run wrappers and RunCollection."""

from __future__ import annotations

from typing import Iterator

from docwow.models.image import InlineImage
from docwow.models.paragraph import BookmarkStart, CrossRef, Hyperlink, ImageRun, PageNumberField, Run, TextRun, TrackedChange
from docwow.models.styles import RunFormatting


class MutableRun:
    """A mutable text run.  Wraps the state of a frozen TextRun."""

    def __init__(
        self,
        text: str = "",
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strike: bool = False,
        small_caps: bool = False,
        all_caps: bool = False,
        font_name: str | None = None,
        font_size: float | None = None,
        color: str | None = None,
        highlight: str | None = None,
        vertical_align: str | None = None,
        char_style_id: str | None = None,
    ) -> None:
        self._text = text
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._strike = strike
        self._small_caps = small_caps
        self._all_caps = all_caps
        self._font_name = font_name
        self._font_size = font_size
        self._color = color
        self._highlight = highlight
        self._vertical_align = vertical_align
        self._char_style_id = char_style_id

    # ---- Text ----------------------------------------------------------------

    def get_text(self) -> str:
        """Return the run's text content."""
        return self._text

    def set_text(self, text: str) -> "MutableRun":
        """Replace the run's text content."""
        self._text = text
        return self

    # ---- Boolean toggles -----------------------------------------------------

    def set_bold(self, value: bool = True) -> "MutableRun":
        """Set bold formatting."""
        self._bold = value
        return self

    def set_italic(self, value: bool = True) -> "MutableRun":
        """Set italic formatting."""
        self._italic = value
        return self

    def set_underline(self, value: bool = True) -> "MutableRun":
        """Set underline formatting."""
        self._underline = value
        return self

    def set_strike(self, value: bool = True) -> "MutableRun":
        """Set strikethrough formatting."""
        self._strike = value
        return self

    def set_small_caps(self, value: bool = True) -> "MutableRun":
        """Set small-caps formatting (renders lowercase letters as smaller uppercase)."""
        self._small_caps = value
        return self

    def set_all_caps(self, value: bool = True) -> "MutableRun":
        """Set all-caps formatting (renders all letters as uppercase)."""
        self._all_caps = value
        return self

    # ---- Font ----------------------------------------------------------------

    def set_font_name(self, name: str | None) -> "MutableRun":
        """Set the font family name."""
        self._font_name = name
        return self

    def set_font_size(self, pt: float | None) -> "MutableRun":
        """Set the font size in points."""
        self._font_size = pt
        return self

    # ---- Color ---------------------------------------------------------------

    def set_color(self, hex_rgb: str | None) -> "MutableRun":
        """Set the text color as a hex RGB string (e.g. 'FF0000')."""
        self._color = hex_rgb
        return self

    def set_highlight(self, color_name: str | None) -> "MutableRun":
        """Set the highlight color name (e.g. 'yellow')."""
        self._highlight = color_name
        return self

    # ---- Vertical alignment --------------------------------------------------

    def set_vertical_align(self, value: str | None) -> "MutableRun":
        """Set vertical alignment: 'superscript', 'subscript', or None."""
        if value not in ("superscript", "subscript", None):
            raise ValueError(
                f"vertical_align must be 'superscript', 'subscript', or None; got {value!r}"
            )
        self._vertical_align = value
        return self

    # ---- Character style -----------------------------------------------------

    def set_char_style(self, style_id: str | None) -> "MutableRun":
        """Apply a named Word character style (e.g. ``'Strong'``, ``'Emphasis'``) or ``None`` to clear."""
        self._char_style_id = style_id
        return self

    # ---- Read-back properties ------------------------------------------------

    @property
    def bold(self) -> bool:
        """True if the run is bold."""
        return self._bold

    @property
    def italic(self) -> bool:
        """True if the run is italic."""
        return self._italic

    @property
    def underline(self) -> bool:
        """True if the run is underlined."""
        return self._underline

    @property
    def strike(self) -> bool:
        """True if the run has strikethrough."""
        return self._strike

    @property
    def small_caps(self) -> bool:
        """True if the run uses small-caps formatting."""
        return self._small_caps

    @property
    def all_caps(self) -> bool:
        """True if the run uses all-caps formatting."""
        return self._all_caps

    @property
    def font_name(self) -> str | None:
        """Font family name, or None to inherit from the style."""
        return self._font_name

    @property
    def font_size(self) -> float | None:
        """Font size in points, or None to inherit from the style."""
        return self._font_size

    @property
    def color(self) -> str | None:
        """Text colour as a 6-digit hex RGB string (e.g. ``'FF0000'``), or None."""
        return self._color

    @property
    def highlight(self) -> str | None:
        """Highlight colour name (e.g. ``'yellow'``, ``'cyan'``), or None."""
        return self._highlight

    @property
    def vertical_align(self) -> str | None:
        """Vertical alignment: ``'superscript'``, ``'subscript'``, or None."""
        return self._vertical_align

    @property
    def char_style_id(self) -> str | None:
        """Named Word character style ID (e.g. ``'Strong'``, ``'Emphasis'``), or None."""
        return self._char_style_id

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> TextRun:
        """Convert to a frozen TextRun for pipeline use."""
        return TextRun(
            text=self._text,
            formatting=RunFormatting(
                bold=self._bold,
                italic=self._italic,
                underline=self._underline,
                strike=self._strike,
                small_caps=self._small_caps,
                all_caps=self._all_caps,
                font_name=self._font_name,
                font_size_pt=self._font_size,
                color=self._color,
                highlight=self._highlight,
                vertical_align=self._vertical_align,
                char_style_id=self._char_style_id,
            ),
        )

    def __repr__(self) -> str:
        flags = []
        if self._bold:
            flags.append("bold")
        if self._italic:
            flags.append("italic")
        if self._underline:
            flags.append("underline")
        suffix = f", {', '.join(flags)}" if flags else ""
        return f"MutableRun({self._text!r}{suffix})"


class MutableImageRun:
    """A mutable inline image run."""

    def __init__(self, image: InlineImage) -> None:
        self._image = image

    def get_image(self) -> InlineImage:
        """Return the underlying InlineImage."""
        return self._image

    def replace_image(
        self,
        data: bytes,
        content_type: str,
        width_pt: float | None = None,
        height_pt: float | None = None,
        alt_text: str = "",
    ) -> "MutableImageRun":
        """Replace the image bytes and optionally update dimensions."""
        self._image = InlineImage(
            relationship_id=f"rId_api_{id(self)}",
            content_type=content_type,
            data=data,
            width_pt=width_pt if width_pt is not None else self._image.width_pt,
            height_pt=height_pt if height_pt is not None else self._image.height_pt,
            alt_text=alt_text,
        )
        return self

    def set_width_pt(self, width_pt: float) -> "MutableImageRun":
        """Set the rendered width in points. Other image properties are unchanged."""
        self._image = InlineImage(
            relationship_id=self._image.relationship_id,
            content_type=self._image.content_type,
            data=self._image.data,
            width_pt=width_pt,
            height_pt=self._image.height_pt,
            alt_text=self._image.alt_text,
        )
        return self

    def set_height_pt(self, height_pt: float) -> "MutableImageRun":
        """Set the rendered height in points. Other image properties are unchanged."""
        self._image = InlineImage(
            relationship_id=self._image.relationship_id,
            content_type=self._image.content_type,
            data=self._image.data,
            width_pt=self._image.width_pt,
            height_pt=height_pt,
            alt_text=self._image.alt_text,
        )
        return self

    def set_alt_text(self, alt_text: str) -> "MutableImageRun":
        """Set the image alt text description. Other image properties are unchanged."""
        self._image = InlineImage(
            relationship_id=self._image.relationship_id,
            content_type=self._image.content_type,
            data=self._image.data,
            width_pt=self._image.width_pt,
            height_pt=self._image.height_pt,
            alt_text=alt_text,
        )
        return self

    @property
    def width_pt(self) -> float:
        """Rendered width in points."""
        return self._image.width_pt

    @property
    def height_pt(self) -> float:
        """Rendered height in points."""
        return self._image.height_pt

    @property
    def alt_text(self) -> str:
        """Image alt text / description."""
        return self._image.alt_text

    @property
    def content_type(self) -> str:
        """MIME type of the image (e.g. ``'image/png'``, ``'image/jpeg'``)."""
        return self._image.content_type

    def _to_frozen(self) -> ImageRun:
        """Convert to a frozen ImageRun for pipeline use."""
        return ImageRun(image=self._image)

    def __repr__(self) -> str:
        return (
            f"MutableImageRun({self._image.content_type!r}, "
            f"{self._image.width_pt:.1f}x{self._image.height_pt:.1f}pt)"
        )


class MutableHyperlink:
    """A mutable hyperlink run with a single text string and a URL."""

    def __init__(self, text: str = "", url: str = "") -> None:
        self._text = text
        self._url = url

    # ---- Setters -------------------------------------------------------------

    def set_text(self, text: str) -> "MutableHyperlink":
        """Replace the link text."""
        self._text = text
        return self

    def set_url(self, url: str) -> "MutableHyperlink":
        """Replace the hyperlink URL."""
        self._url = url
        return self

    # ---- Read-back -----------------------------------------------------------

    def get_text(self) -> str:
        """Return the link text."""
        return self._text

    @property
    def url(self) -> str:
        """The hyperlink URL."""
        return self._url

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> Hyperlink:
        """Convert to a frozen Hyperlink for pipeline use."""
        return Hyperlink(
            url=self._url,
            runs=(TextRun(text=self._text),) if self._text else (),
        )

    def __repr__(self) -> str:
        return f"MutableHyperlink({self._text!r}, url={self._url!r})"


class MutablePageNumberField:
    """A mutable page-number field (PAGE, NUMPAGES, SECTIONPAGES)."""

    _VALID_TYPES = ("PAGE", "NUMPAGES", "SECTIONPAGES")

    def __init__(self, field_type: str = "PAGE") -> None:
        if field_type not in self._VALID_TYPES:
            raise ValueError(
                f"field_type must be one of {self._VALID_TYPES}; got {field_type!r}"
            )
        self._field_type = field_type

    @property
    def field_type(self) -> str:
        """The field type: ``'PAGE'``, ``'NUMPAGES'``, or ``'SECTIONPAGES'``."""
        return self._field_type

    def set_field_type(self, field_type: str) -> "MutablePageNumberField":
        """Change the field type."""
        if field_type not in self._VALID_TYPES:
            raise ValueError(
                f"field_type must be one of {self._VALID_TYPES}; got {field_type!r}"
            )
        self._field_type = field_type
        return self

    def _to_frozen(self) -> PageNumberField:
        return PageNumberField(field_type=self._field_type)

    def __repr__(self) -> str:
        return f"MutablePageNumberField({self._field_type!r})"


class MutableBookmark:
    """A mutable bookmark anchor.

    When converted to a frozen model (at save time) this produces a
    :class:`~docwow.models.paragraph.BookmarkStart` which the writer
    renders as a ``<w:bookmarkStart>`` / ``<w:bookmarkEnd>`` pair.
    """

    def __init__(self, name: str = "") -> None:
        self._name = name

    # ---- Setter --------------------------------------------------------------

    def set_name(self, name: str) -> "MutableBookmark":
        """Replace the bookmark name."""
        self._name = name
        return self

    # ---- Read-back -----------------------------------------------------------

    @property
    def name(self) -> str:
        """The bookmark name used as the HTML ``id`` and OOXML ``w:name``."""
        return self._name

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> BookmarkStart:
        """Convert to a frozen BookmarkStart for pipeline use."""
        return BookmarkStart(name=self._name)

    def __repr__(self) -> str:
        return f"MutableBookmark({self._name!r})"


class MutableCrossRef:
    """A mutable cross-reference field (REF) linking to a named bookmark."""

    def __init__(self, bookmark_name: str = "", display_text: str = "") -> None:
        self._bookmark_name = bookmark_name
        self._display_text = display_text

    # ---- Setters -------------------------------------------------------------

    def set_bookmark_name(self, name: str) -> "MutableCrossRef":
        """Set the target bookmark name."""
        self._bookmark_name = name
        return self

    def set_display_text(self, text: str) -> "MutableCrossRef":
        """Set the display text shown at the field location."""
        self._display_text = text
        return self

    # ---- Read-back -----------------------------------------------------------

    @property
    def bookmark_name(self) -> str:
        """The target bookmark name."""
        return self._bookmark_name

    @property
    def display_text(self) -> str:
        """The text displayed at the cross-reference location."""
        return self._display_text

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> CrossRef:
        """Convert to a frozen CrossRef for pipeline use."""
        return CrossRef(bookmark_name=self._bookmark_name, display_text=self._display_text)

    def __repr__(self) -> str:
        return f"MutableCrossRef({self._bookmark_name!r}, {self._display_text!r})"


class MutableTrackedChange:
    """A mutable tracked change (insertion or deletion).

    Wraps a ``w:ins`` or ``w:del`` element.  ``change_type`` is either
    ``"insert"`` or ``"delete"``.

    Create via :meth:`RunCollection.add_insertion` or
    :meth:`RunCollection.add_deletion` rather than instantiating directly.
    """

    def __init__(
        self,
        change_type: str,
        text: str = "",
        author: str = "",
        date: str = "",
        change_id: int = 0,
    ) -> None:
        if change_type not in ("insert", "delete"):
            raise ValueError(f"change_type must be 'insert' or 'delete'; got {change_type!r}")
        self._change_type = change_type
        self._text = text
        self._author = author
        self._date = date
        self._change_id = change_id

    # ---- Setters -------------------------------------------------------------

    def set_text(self, text: str) -> "MutableTrackedChange":
        """Replace the changed text."""
        self._text = text
        return self

    def set_author(self, author: str) -> "MutableTrackedChange":
        """Set the author name."""
        self._author = author
        return self

    def set_date(self, date: str) -> "MutableTrackedChange":
        """Set the ISO-8601 date string."""
        self._date = date
        return self

    # ---- Read-back -----------------------------------------------------------

    def get_text(self) -> str:
        """Return the changed text."""
        return self._text

    @property
    def change_type(self) -> str:
        """Either ``'insert'`` or ``'delete'``."""
        return self._change_type

    @property
    def author(self) -> str:
        """Reviewer display name."""
        return self._author

    @property
    def date(self) -> str:
        """ISO-8601 datetime string of the change."""
        return self._date

    @property
    def change_id(self) -> int:
        """OOXML ``w:id`` for this change (0 = auto-assigned on write)."""
        return self._change_id

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> TrackedChange:
        """Convert to a frozen TrackedChange for pipeline use."""
        return TrackedChange(
            change_type=self._change_type,
            runs=(TextRun(text=self._text),),
            author=self._author,
            date=self._date,
            change_id=self._change_id,
        )

    def __repr__(self) -> str:
        return (
            f"MutableTrackedChange({self._change_type!r}, "
            f"{self._text!r}, author={self._author!r})"
        )


class RunCollection:
    """Ordered mutable collection of run instances."""

    _ALLOWED = (MutableRun, MutableImageRun, MutableHyperlink, MutablePageNumberField, MutableBookmark, MutableCrossRef)

    _AnyRun = MutableRun | MutableImageRun | MutableHyperlink | MutablePageNumberField | MutableBookmark | MutableCrossRef

    def __init__(self) -> None:
        self._items: list[RunCollection._AnyRun] = []

    # ---- Sequence protocol ---------------------------------------------------

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[_AnyRun]:
        return iter(self._items)

    def __getitem__(self, index: int) -> _AnyRun:
        return self._items[index]

    # ---- Mutation ------------------------------------------------------------

    def append(self, run: _AnyRun) -> None:
        """Append a run to the end of the collection."""
        self._check_type(run)
        self._items.append(run)

    def insert(self, index: int, run: _AnyRun) -> None:
        """Insert a run at the given index."""
        self._check_type(run)
        self._items.insert(index, run)

    def remove(self, index: int) -> None:
        """Remove the run at the given index."""
        del self._items[index]

    def clear(self) -> None:
        """Remove all runs."""
        self._items.clear()

    # ---- Convenience factories -----------------------------------------------

    def add_text(
        self,
        text: str,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strike: bool = False,
        small_caps: bool = False,
        all_caps: bool = False,
        font_name: str | None = None,
        font_size: float | None = None,
        color: str | None = None,
        highlight: str | None = None,
        vertical_align: str | None = None,
        char_style_id: str | None = None,
    ) -> MutableRun:
        """Create a MutableRun, append it, and return it."""
        run = MutableRun(
            text=text,
            bold=bold,
            italic=italic,
            underline=underline,
            strike=strike,
            small_caps=small_caps,
            all_caps=all_caps,
            font_name=font_name,
            font_size=font_size,
            color=color,
            highlight=highlight,
            vertical_align=vertical_align,
            char_style_id=char_style_id,
        )
        self._items.append(run)
        return run

    def add_hyperlink(self, text: str, url: str) -> MutableHyperlink:
        """Create a MutableHyperlink, append it, and return it."""
        link = MutableHyperlink(text=text, url=url)
        self._items.append(link)
        return link

    def add_page_number(self, field_type: str = "PAGE") -> MutablePageNumberField:
        """Create a MutablePageNumberField, append it, and return it.

        Args:
            field_type: One of ``'PAGE'``, ``'NUMPAGES'``, ``'SECTIONPAGES'``.
        """
        field = MutablePageNumberField(field_type=field_type)
        self._items.append(field)
        return field

    def add_bookmark(self, name: str) -> MutableBookmark:
        """Create a bookmark anchor, append it, and return it.

        Args:
            name: The bookmark name used as the ``id`` attribute in HTML and
                  the ``w:name`` attribute in OOXML.  Must be unique within
                  the document.
        """
        bm = MutableBookmark(name=name)
        self._items.append(bm)
        return bm

    def add_cross_ref(self, bookmark_name: str, display_text: str = "") -> MutableCrossRef:
        """Create a cross-reference to a named bookmark, append it, and return it.

        Args:
            bookmark_name: The target bookmark name (must match a ``MutableBookmark``
                           elsewhere in the document).
            display_text:  The text displayed at the reference location.  Falls back
                           to ``bookmark_name`` if empty.
        """
        ref = MutableCrossRef(bookmark_name=bookmark_name, display_text=display_text)
        self._items.append(ref)
        return ref

    def add_footnote_ref(self, note_id: int, note_type: str = "footnote") -> "MutableFootnoteRef":
        """Create a footnote or endnote reference marker, append it, and return it.

        Args:
            note_id:   The integer ID of the note this marker points to.
            note_type: ``'footnote'`` (default) or ``'endnote'``.
        """
        from docwow.api.footnote import MutableFootnoteRef
        ref = MutableFootnoteRef(note_id=note_id, note_type=note_type)
        self._items.append(ref)
        return ref

    def add_comment_ref(self, comment_id: int) -> "MutableCommentRef":
        """Create a comment reference marker, append it, and return it.

        Args:
            comment_id: The integer ID of the comment this marker points to.
        """
        from docwow.api.comment import MutableCommentRef
        ref = MutableCommentRef(comment_id=comment_id)
        self._items.append(ref)
        return ref

    def add_insertion(
        self,
        text: str,
        author: str = "",
        date: str = "",
        change_id: int = 0,
    ) -> MutableTrackedChange:
        """Create a tracked insertion, append it, and return it.

        In HTML this renders as a green-underlined ``<ins>`` element.
        In DOCX it becomes a ``<w:ins>`` element visible in Word's review pane.

        Args:
            text:      The inserted text.
            author:    Reviewer name shown in Word's review pane.
            date:      ISO-8601 timestamp string (e.g. ``"2025-07-10T09:00:00Z"``).
            change_id: Optional integer ID; auto-assigned on write if 0.
        """
        tc = MutableTrackedChange("insert", text=text, author=author, date=date, change_id=change_id)
        self._items.append(tc)
        return tc

    def add_deletion(
        self,
        text: str,
        author: str = "",
        date: str = "",
        change_id: int = 0,
    ) -> MutableTrackedChange:
        """Create a tracked deletion, append it, and return it.

        In HTML this renders as a red-strikethrough ``<del>`` element.
        In DOCX it becomes a ``<w:del>`` element visible in Word's review pane.

        Args:
            text:      The deleted text.
            author:    Reviewer name shown in Word's review pane.
            date:      ISO-8601 timestamp string.
            change_id: Optional integer ID; auto-assigned on write if 0.
        """
        tc = MutableTrackedChange("delete", text=text, author=author, date=date, change_id=change_id)
        self._items.append(tc)
        return tc

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> tuple[Run, ...]:
        """Convert all runs to frozen models."""
        return tuple(r._to_frozen() for r in self._items)

    # ---- Type enforcement ----------------------------------------------------

    def _check_type(self, run: object) -> None:
        from docwow.api.footnote import MutableFootnoteRef
        from docwow.api.comment import MutableCommentRef
        allowed = self._ALLOWED + (MutableFootnoteRef, MutableCommentRef, MutableTrackedChange)
        if not isinstance(run, allowed):
            if isinstance(run, (TextRun, ImageRun, Hyperlink, PageNumberField, CrossRef, BookmarkStart, TrackedChange)):
                raise TypeError(
                    f"Cannot add a frozen {type(run).__name__} directly. "
                    "Use MutableRun, MutableHyperlink, MutablePageNumberField, MutableCrossRef, "
                    "MutableBookmark, or the add_* factory methods instead."
                )
            raise TypeError(
                f"Expected MutableRun, MutableImageRun, MutableHyperlink, "
                f"MutablePageNumberField, MutableBookmark, MutableFootnoteRef, "
                f"MutableCommentRef, or MutableTrackedChange; got {type(run).__name__!r}"
            )

    def __repr__(self) -> str:
        return f"RunCollection({len(self._items)} runs)"
