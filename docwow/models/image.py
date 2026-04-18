from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InlineImage:
    """An inline image embedded in a paragraph run."""

    relationship_id: str   # rId key from the DOCX relationships file
    content_type: str      # MIME type e.g. "image/png", "image/jpeg"
    data: bytes            # raw image bytes
    width_pt: float        # rendered width in points (converted from EMU at parse time)
    height_pt: float       # rendered height in points (converted from EMU at parse time)
    alt_text: str = ""     # accessibility description


@dataclass(frozen=True)
class FloatingImage:
    """A floating (anchored) image positioned relative to the page or margin.

    Corresponds to ``wp:anchor`` in OOXML.  The image floats outside the normal
    text flow and is positioned by ``pos_h`` / ``pos_v`` offsets (in points)
    relative to ``h_anchor`` / ``v_anchor`` (e.g. ``"page"``, ``"margin"``,
    ``"column"``).

    ``wrap`` is the text-wrapping mode:

    * ``"none"``          — image overlaps text (``wp:wrapNone``)
    * ``"square"``        — text wraps in a rectangle around the image
    * ``"tight"``         — text wraps tightly around the image outline
    * ``"topAndBottom"``  — text above and below, not beside the image
    * ``"through"``       — text flows through transparent areas
    """

    relationship_id: str
    content_type: str
    data: bytes
    width_pt: float
    height_pt: float
    pos_h_pt: float = 0.0           # horizontal offset from anchor in points
    pos_v_pt: float = 0.0           # vertical offset from anchor in points
    h_anchor: str = "column"        # "margin", "page", "column", "character"
    v_anchor: str = "paragraph"     # "margin", "page", "paragraph", "line"
    wrap: str = "square"            # see docstring above
    behind_doc: bool = False        # z-order: behind body text
    alt_text: str = ""
