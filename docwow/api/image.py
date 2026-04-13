"""Mutable image wrapper (top-level image paragraph)."""

from __future__ import annotations

from docwow.models.image import InlineImage
from docwow.models.paragraph import ImageRun, Paragraph
from docwow.api.paragraph import MutableParagraph
from docwow.api.run import MutableImageRun, RunCollection


class MutableImage(MutableParagraph):
    """
    A top-level image in the document body.

    Internally represented as a single-run paragraph containing an ImageRun,
    which is how DOCX stores block-level images.  For inline images within
    text, add a MutableImageRun directly to a paragraph's RunCollection.
    """

    def __init__(
        self,
        data: bytes,
        content_type: str,
        width_pt: float,
        height_pt: float,
        alt_text: str = "",
        relationship_id: str = "",
    ) -> None:
        super().__init__()
        rid = relationship_id or f"rId_api_{id(self)}"
        image = InlineImage(
            relationship_id=rid,
            content_type=content_type,
            data=data,
            width_pt=width_pt,
            height_pt=height_pt,
            alt_text=alt_text,
        )
        self._image_run = MutableImageRun(image)
        self._runs.append(self._image_run)

    def replace(
        self,
        data: bytes,
        content_type: str,
        width_pt: float | None = None,
        height_pt: float | None = None,
        alt_text: str = "",
    ) -> "MutableImage":
        """Replace the image content, optionally updating dimensions."""
        self._image_run.replace_image(
            data=data,
            content_type=content_type,
            width_pt=width_pt,
            height_pt=height_pt,
            alt_text=alt_text,
        )
        return self

    @property
    def width_pt(self) -> float:
        return self._image_run.width_pt

    @property
    def height_pt(self) -> float:
        return self._image_run.height_pt

    @property
    def alt_text(self) -> str:
        return self._image_run.alt_text

    @property
    def content_type(self) -> str:
        return self._image_run.content_type

    def __repr__(self) -> str:
        return (
            f"MutableImage({self._image_run.content_type!r}, "
            f"{self._image_run.width_pt:.1f}x{self._image_run.height_pt:.1f}pt)"
        )
