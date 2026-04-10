"""Render an InlineImage to an HTML <img> element with a base64 data URI."""

from __future__ import annotations

import base64

from docwow.models.image import InlineImage
from docwow.utils.units import pt_to_css


def render_image(image: InlineImage) -> str:
    """Return an <img> element with an embedded base64 data URI.

    Visual size is set via inline style (width/height in pt).
    All Word metadata is preserved in data-dw-* attributes for round-trip.
    """
    b64 = base64.b64encode(image.data).decode("ascii")
    src = f"data:{image.content_type};base64,{b64}"

    width_css = pt_to_css(image.width_pt)
    height_css = pt_to_css(image.height_pt)

    attrs: list[str] = [
        f'class="dw-img"',
        f'src="{src}"',
        f'alt="{_escape_attr(image.alt_text)}"',
        f'style="width:{width_css};height:{height_css};vertical-align:middle"',
        f'data-dw-rid="{_escape_attr(image.relationship_id)}"',
        f'data-dw-width="{width_css}"',
        f'data-dw-height="{height_css}"',
    ]

    return f'<img {" ".join(attrs)}>'


def _escape_attr(value: str) -> str:
    """Escape a string for use inside a double-quoted HTML attribute."""
    return (
        value
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
