from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SectionProperties:
    """Page geometry for a single section."""

    page_width_pt: float = 595.28   # A4 width
    page_height_pt: float = 841.89  # A4 height
    margin_top_pt: float = 72.0
    margin_bottom_pt: float = 72.0
    margin_left_pt: float = 72.0
    margin_right_pt: float = 72.0
    break_type: str = "nextPage"    # "nextPage" | "evenPage" | "oddPage" | "continuous"


@dataclass(frozen=True)
class SectionBreak:
    """An inline section break — marks the end of one section and the start of another.

    ``properties`` describes the PRECEDING section's page geometry and how the
    break transitions to the next section.  In OOXML this is stored as
    ``w:sectPr`` inside the ``w:pPr`` of the last paragraph of that section.
    """

    properties: SectionProperties = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.properties is None:
            object.__setattr__(self, "properties", SectionProperties())
