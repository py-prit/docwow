"""Render InlineImage / FloatingImage to HTML <img> / <figure> elements."""

from __future__ import annotations

import base64

from docwow.models.image import FloatingImage, InlineImage
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


def render_floating_image(image: FloatingImage) -> str:
    """Return a ``<figure>`` element for a floating image.

    The figure uses CSS ``float:left`` / ``float:right`` for ``square`` and
    ``topAndBottom`` wraps, and ``position:relative`` for others.
    ``data-dw-float-*`` attributes carry all positioning metadata for
    lossless round-trip back to ``wp:anchor``.
    """
    b64 = base64.b64encode(image.data).decode("ascii")
    src = f"data:{image.content_type};base64,{b64}"

    width_css = pt_to_css(image.width_pt)
    height_css = pt_to_css(image.height_pt)

    # Choose a CSS presentation that approximates the wrap mode in browsers.
    # Exact page-level positioning is not reproducible without a layout engine;
    # we capture the DOCX metadata verbatim so the round-trip is lossless.
    wrap = image.wrap
    if wrap in ("square", "tight", "through"):
        # Float direction: if pos_h_pt is past the centre of a typical page
        # (> ~220pt from left margin) treat as right-floated, else left.
        direction = "right" if image.pos_h_pt > 220 else "left"
        figure_style = f"float:{direction};margin:4pt;"
    elif wrap == "topAndBottom":
        figure_style = "display:block;margin:8pt auto;"
    else:  # "none" — overlapping; show inline so it's at least visible
        figure_style = "display:inline-block;"

    img_attrs = " ".join([
        f'src="{src}"',
        f'alt="{_escape_attr(image.alt_text)}"',
        f'style="width:{width_css};height:{height_css};display:block"',
    ])

    figure_attrs = " ".join([
        'class="dw-float-img"',
        f'style="{figure_style}"',
        f'data-dw-float-wrap="{wrap}"',
        f'data-dw-float-h-anchor="{image.h_anchor}"',
        f'data-dw-float-v-anchor="{image.v_anchor}"',
        f'data-dw-float-pos-h="{pt_to_css(image.pos_h_pt)}"',
        f'data-dw-float-pos-v="{pt_to_css(image.pos_v_pt)}"',
        f'data-dw-float-behind="{"true" if image.behind_doc else "false"}"',
        f'data-dw-rid="{_escape_attr(image.relationship_id)}"',
        f'data-dw-width="{width_css}"',
        f'data-dw-height="{height_css}"',
    ])

    return f'<figure {figure_attrs}><img {img_attrs}></figure>'


def _escape_attr(value: str) -> str:
    """Escape a string for use inside a double-quoted HTML attribute."""
    return (
        value
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
