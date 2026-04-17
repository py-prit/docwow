"""Mutable wrappers for Table of Contents models."""

from __future__ import annotations

from docwow.models.toc import TableOfContents, TocEntry


class MutableTocEntry:
    """A mutable entry in a Table of Contents."""

    def __init__(self, text: str = "", url: str = "", level: int = 1) -> None:
        self._text = text
        self._url = url
        self._level = level

    # ---- Properties ----------------------------------------------------------

    @property
    def text(self) -> str:
        """Visible label of this entry."""
        return self._text

    @property
    def url(self) -> str:
        """Anchor target URL (e.g. ``"#_Toc123"``) or empty string."""
        return self._url

    @property
    def level(self) -> int:
        """Hierarchy depth, 1–9."""
        return self._level

    # ---- Setters -------------------------------------------------------------

    def set_text(self, text: str) -> "MutableTocEntry":
        """Set the display text. Returns self for chaining."""
        self._text = text
        return self

    def set_url(self, url: str) -> "MutableTocEntry":
        """Set the anchor URL. Returns self for chaining."""
        self._url = url
        return self

    def set_level(self, level: int) -> "MutableTocEntry":
        """Set the depth level (1–9). Returns self for chaining."""
        if not 1 <= level <= 9:
            raise ValueError(f"level must be between 1 and 9; got {level!r}")
        self._level = level
        return self

    # ---- Conversion ----------------------------------------------------------

    def _to_frozen(self) -> TocEntry:
        """Convert to a frozen :class:`~docwow.models.toc.TocEntry`."""
        return TocEntry(text=self._text, url=self._url, level=self._level)

    def __repr__(self) -> str:
        return f"MutableTocEntry(level={self._level!r}, text={self._text!r})"


class MutableTableOfContents:
    """A mutable Table of Contents.

    Wraps a :class:`~docwow.models.toc.TableOfContents` and provides a
    chainable API for editing TOC entries.

    Example::

        toc = MutableTableOfContents(title="Contents")
        toc.add_entry("Introduction", url="#_Toc1", level=1)
        toc.add_entry("Background", url="#_Toc2", level=2)
    """

    def __init__(
        self,
        title: str = "Contents",
        entries: list[MutableTocEntry] | None = None,
    ) -> None:
        self._title = title
        self._entries: list[MutableTocEntry] = list(entries) if entries else []

    # ---- Properties ----------------------------------------------------------

    @property
    def title(self) -> str:
        """Heading text shown above the entry list."""
        return self._title

    @property
    def entries(self) -> list[MutableTocEntry]:
        """Ordered list of :class:`MutableTocEntry` objects."""
        return self._entries

    # ---- Setters -------------------------------------------------------------

    def set_title(self, title: str) -> "MutableTableOfContents":
        """Set the TOC heading text. Returns self for chaining."""
        self._title = title
        return self

    # ---- Factories -----------------------------------------------------------

    def add_entry(
        self,
        text: str,
        url: str = "",
        level: int = 1,
    ) -> MutableTocEntry:
        """Append a new entry and return it.

        Args:
            text:  Visible label of the entry.
            url:   Anchor target (e.g. ``"#_Toc123"``).  Defaults to ``""``.
            level: Depth (1–9).  Defaults to ``1``.
        """
        entry = MutableTocEntry(text=text, url=url, level=level)
        self._entries.append(entry)
        return entry

    # ---- Conversion ----------------------------------------------------------

    def _to_frozen(self) -> TableOfContents:
        """Convert to a frozen :class:`~docwow.models.toc.TableOfContents`."""
        return TableOfContents(
            title=self._title,
            entries=tuple(e._to_frozen() for e in self._entries),
        )

    def __repr__(self) -> str:
        return (
            f"MutableTableOfContents(title={self._title!r}, "
            f"entries={len(self._entries)})"
        )
