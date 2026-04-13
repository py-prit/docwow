"""Mutable run wrappers and RunCollection."""

from __future__ import annotations

from typing import Iterator

from docwow.models.image import InlineImage
from docwow.models.paragraph import Hyperlink, ImageRun, PageNumberField, Run, TextRun
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
        font_name: str | None = None,
        font_size: float | None = None,
        color: str | None = None,
        highlight: str | None = None,
        vertical_align: str | None = None,
    ) -> None:
        self._text = text
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._strike = strike
        self._font_name = font_name
        self._font_size = font_size
        self._color = color
        self._highlight = highlight
        self._vertical_align = vertical_align

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

    # ---- Read-back properties ------------------------------------------------

    @property
    def bold(self) -> bool:
        return self._bold

    @property
    def italic(self) -> bool:
        return self._italic

    @property
    def underline(self) -> bool:
        return self._underline

    @property
    def strike(self) -> bool:
        return self._strike

    @property
    def font_name(self) -> str | None:
        return self._font_name

    @property
    def font_size(self) -> float | None:
        return self._font_size

    @property
    def color(self) -> str | None:
        return self._color

    @property
    def highlight(self) -> str | None:
        return self._highlight

    @property
    def vertical_align(self) -> str | None:
        return self._vertical_align

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
                font_name=self._font_name,
                font_size_pt=self._font_size,
                color=self._color,
                highlight=self._highlight,
                vertical_align=self._vertical_align,
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

    @property
    def width_pt(self) -> float:
        return self._image.width_pt

    @property
    def height_pt(self) -> float:
        return self._image.height_pt

    @property
    def alt_text(self) -> str:
        return self._image.alt_text

    @property
    def content_type(self) -> str:
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


class RunCollection:
    """Ordered mutable collection of run instances."""

    _ALLOWED = (MutableRun, MutableImageRun, MutableHyperlink, MutablePageNumberField)

    _AnyRun = MutableRun | MutableImageRun | MutableHyperlink | MutablePageNumberField

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
        font_name: str | None = None,
        font_size: float | None = None,
        color: str | None = None,
        highlight: str | None = None,
        vertical_align: str | None = None,
    ) -> MutableRun:
        """Create a MutableRun, append it, and return it."""
        run = MutableRun(
            text=text,
            bold=bold,
            italic=italic,
            underline=underline,
            strike=strike,
            font_name=font_name,
            font_size=font_size,
            color=color,
            highlight=highlight,
            vertical_align=vertical_align,
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

    # ---- Internal conversion -------------------------------------------------

    def _to_frozen(self) -> tuple[Run, ...]:
        """Convert all runs to frozen models."""
        return tuple(r._to_frozen() for r in self._items)

    # ---- Type enforcement ----------------------------------------------------

    def _check_type(self, run: object) -> None:
        if not isinstance(run, self._ALLOWED):
            if isinstance(run, (TextRun, ImageRun, Hyperlink, PageNumberField)):
                raise TypeError(
                    f"Cannot add a frozen {type(run).__name__} directly. "
                    "Use MutableRun, MutableHyperlink, MutablePageNumberField, "
                    "or the add_* factory methods instead."
                )
            raise TypeError(
                f"Expected MutableRun, MutableImageRun, MutableHyperlink, or "
                f"MutablePageNumberField; got {type(run).__name__!r}"
            )

    def __repr__(self) -> str:
        return f"RunCollection({len(self._items)} runs)"
