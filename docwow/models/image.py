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
