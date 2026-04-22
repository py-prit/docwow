from __future__ import annotations

from dataclasses import dataclass

from docwow.models.styles import RunFormatting


@dataclass(frozen=True)
class ListLevel:
    """Formatting definition for one level of a numbered/bulleted list (0-based)."""

    level: int       # 0–8 (Word supports up to 9 levels)
    num_fmt: str     # "bullet" | "decimal" | "lowerLetter" | "upperLetter"
                     # | "lowerRoman" | "upperRoman" | "none"
    start_value: int = 1
    text_template: str = "%1."   # e.g. "%1." → "1.", "%1.%2." → "1.1."
    indent_pt: float = 0.0       # left indent for the list item text
    hanging_pt: float = 0.0      # hanging indent (bullet/number protrudes left)
    suff: str = "tab"            # separator after label: "tab" | "space" | "nothing"
    run_fmt: RunFormatting | None = None   # formatting applied to the list label


@dataclass(frozen=True)
class NumberingDefinition:
    """Maps an abstract numbering definition to its per-level configurations."""

    abstract_num_id: str
    levels: tuple[ListLevel, ...]


@dataclass(frozen=True)
class ListInfo:
    """Attached to a Paragraph when it is a list item."""

    num_id: str    # references a NumberingDefinition via its concrete num ID
    level: int     # 0-based level in the list hierarchy
