"""Header and footer models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docwow.models.paragraph import Paragraph


@dataclass(frozen=True)
class HeaderFooter:
    """An ordered sequence of paragraphs forming a header or footer.

    A document can have up to three header types and three footer types:

    * ``default`` — used on all pages (or all odd pages when even is also set)
    * ``first``   — used on the first page only (requires ``title_pg=True``)
    * ``even``    — used on even-numbered pages (requires mirror margins)
    """

    paragraphs: tuple  # tuple[Paragraph, ...]
