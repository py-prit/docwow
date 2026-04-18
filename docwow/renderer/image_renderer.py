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

    # Choose CSS that faithfully replicates the Word wrap behaviour in a browser.
    # Exact page-level coordinates can't be replicated without a layout engine,
    # but the visual effect of each wrap mode can be achieved with CSS.
    wrap = image.wrap
    z = "-1" if image.behind_doc else "1"

    if wrap in ("square", "tight", "through"):
        # Float left or right based on horizontal position.
        # A typical A4/Letter text column is ~450pt; treat >½ as right-floated.
        direction = "right" if image.pos_h_pt > 220 else "left"
        margin = "margin:0 8pt 4pt 0" if direction == "left" else "margin:0 0 4pt 8pt"
        figure_style = f"float:{direction};{margin};z-index:{z};"
    elif wrap == "topAndBottom":
        # Block with clear on both sides forces text above and below only.
        figure_style = f"display:block;clear:both;margin:8pt auto;z-index:{z};"
    else:
        # wrapNone — image is positioned absolutely relative to the paragraph.
        # The paragraph renderer adds position:relative to the <p> element.
        left = pt_to_css(image.pos_h_pt)
        top = pt_to_css(image.pos_v_pt)
        figure_style = (
            f"position:absolute;left:{left};top:{top};"
            f"z-index:{z};margin:0;"
        )

    img_attrs = " ".join([
        f'src="{src}"',
        f'alt="{_escape_attr(image.alt_text)}"',
        f'style="width:{width_css};height:{height_css};display:block"',
    ])

    common_attrs = " ".join([
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

    if wrap == "none":
        # <figure> is block-level — browsers auto-close the enclosing <p> before it,
        # which breaks position:relative/absolute. Use <span style="display:block">
        # instead: it is phrasing content, valid inside <p>, and stays in the same
        # stacking context as the paragraph.
        return f'<span {common_attrs}><img {img_attrs}></span>'

    return f'<figure {common_attrs}><img {img_attrs}></figure>'


def _escape_attr(value: str) -> str:
    """Escape a string for use inside a double-quoted HTML attribute."""
    return (
        value
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
