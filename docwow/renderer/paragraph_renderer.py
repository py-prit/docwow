"""Render Paragraph and Run objects to HTML."""

from __future__ import annotations

import html

from docwow.models.paragraph import Hyperlink, ImageRun, PageNumberField, Paragraph, Run, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.renderer.image_renderer import render_image
from docwow.utils.units import pt_to_css


def render_paragraph(p: Paragraph, extra_classes: list[str] | None = None) -> str:
    """Return a <p> HTML element for a paragraph."""
    fmt = p.formatting
    classes = ["dw-p"]
    if fmt.style_id:
        classes.append(f"dw-style-{_css_ident(fmt.style_id)}")
    if extra_classes:
        classes.extend(extra_classes)

    data_attrs = _para_data_attrs(fmt)
    if p.list_info is not None:
        data_attrs["data-dw-num-id"] = p.list_info.num_id
        data_attrs["data-dw-level"] = str(p.list_info.level)

    inline_style = _para_inline_style(fmt)
    inner = "".join(_render_run(r) for r in p.runs)

    return _tag("p", classes, data_attrs, inline_style, inner)


def _render_run(run: Run) -> str:
    if isinstance(run, ImageRun):
        return render_image(run.image)
    if isinstance(run, Hyperlink):
        return _render_hyperlink(run)
    if isinstance(run, PageNumberField):
        return _render_page_number_field(run)
    return _render_text_run(run)


def _render_page_number_field(field: PageNumberField) -> str:
    inline_style = _run_inline_style(field.formatting)
    style_attr = f' style="{inline_style}"' if inline_style else ""
    placeholder = "1"  # visual placeholder in HTML
    return (
        f'<span class="dw-field" data-dw-field="{field.field_type}"{style_attr}>'
        f"{placeholder}</span>"
    )


def _render_hyperlink(link: Hyperlink) -> str:
    inner = "".join(_render_text_run(r) for r in link.runs)
    url = html.escape(link.url, quote=True)
    return f'<a href="{url}" class="dw-hyperlink" data-dw-href="{url}">{inner}</a>'


def _render_text_run(run: TextRun) -> str:
    fmt = run.formatting
    classes = ["dw-r"]
    data_attrs = _run_data_attrs(fmt)
    inline_style = _run_inline_style(fmt)
    inner = _escape_text(run.text)
    return _tag("span", classes, data_attrs, inline_style, inner)


# ---------------------------------------------------------------------------
# Attribute builders
# ---------------------------------------------------------------------------

def _para_data_attrs(fmt: ParagraphFormatting) -> dict[str, str]:
    attrs: dict[str, str] = {}
    if fmt.style_id:
        attrs["data-dw-style"] = fmt.style_id
    if fmt.alignment:
        attrs["data-dw-alignment"] = fmt.alignment
    if fmt.indent_left_pt:
        attrs["data-dw-indent-left"] = pt_to_css(fmt.indent_left_pt)
    if fmt.indent_right_pt:
        attrs["data-dw-indent-right"] = pt_to_css(fmt.indent_right_pt)
    if fmt.indent_first_line_pt:
        attrs["data-dw-indent-first-line"] = pt_to_css(fmt.indent_first_line_pt)
    if fmt.space_before_pt:
        attrs["data-dw-space-before"] = pt_to_css(fmt.space_before_pt)
    if fmt.space_after_pt:
        attrs["data-dw-space-after"] = pt_to_css(fmt.space_after_pt)
    if fmt.line_spacing_pt is not None:
        attrs["data-dw-line-spacing"] = pt_to_css(fmt.line_spacing_pt)
    if fmt.keep_together:
        attrs["data-dw-keep-together"] = "true"
    if fmt.keep_with_next:
        attrs["data-dw-keep-with-next"] = "true"
    if fmt.page_break_before:
        attrs["data-dw-page-break-before"] = "true"
    return attrs


def _run_data_attrs(fmt: RunFormatting) -> dict[str, str]:
    attrs: dict[str, str] = {}
    if fmt.bold:
        attrs["data-dw-bold"] = "true"
    if fmt.italic:
        attrs["data-dw-italic"] = "true"
    if fmt.underline:
        attrs["data-dw-underline"] = "true"
    if fmt.strike:
        attrs["data-dw-strike"] = "true"
    if fmt.font_name:
        attrs["data-dw-font-name"] = fmt.font_name
    if fmt.font_size_pt is not None:
        attrs["data-dw-font-size"] = pt_to_css(fmt.font_size_pt)
    if fmt.color:
        attrs["data-dw-color"] = fmt.color
    if fmt.highlight:
        attrs["data-dw-highlight"] = fmt.highlight
    if fmt.vertical_align:
        attrs["data-dw-vertical-align"] = fmt.vertical_align
    return attrs


# ---------------------------------------------------------------------------
# Inline style builders
# ---------------------------------------------------------------------------

def _para_inline_style(fmt: ParagraphFormatting) -> str:
    rules: list[str] = []
    if fmt.alignment:
        rules.append(f"text-align:{fmt.alignment}")
    if fmt.indent_left_pt:
        rules.append(f"padding-left:{pt_to_css(fmt.indent_left_pt)}")
    if fmt.indent_right_pt:
        rules.append(f"padding-right:{pt_to_css(fmt.indent_right_pt)}")
    if fmt.indent_first_line_pt > 0:
        rules.append(f"text-indent:{pt_to_css(fmt.indent_first_line_pt)}")
    if fmt.space_before_pt:
        rules.append(f"margin-top:{pt_to_css(fmt.space_before_pt)}")
    if fmt.space_after_pt:
        rules.append(f"margin-bottom:{pt_to_css(fmt.space_after_pt)}")
    if fmt.line_spacing_pt is not None:
        rules.append(f"line-height:{pt_to_css(fmt.line_spacing_pt)}")
    return ";".join(rules)


def _run_inline_style(fmt: RunFormatting) -> str:
    rules: list[str] = []
    if fmt.bold:
        rules.append("font-weight:bold")
    if fmt.italic:
        rules.append("font-style:italic")
    decorations: list[str] = []
    if fmt.underline:
        decorations.append("underline")
    if fmt.strike:
        decorations.append("line-through")
    if decorations:
        rules.append(f"text-decoration:{' '.join(decorations)}")
    if fmt.font_name:
        rules.append(f"font-family:{fmt.font_name}")
    if fmt.font_size_pt is not None:
        rules.append(f"font-size:{pt_to_css(fmt.font_size_pt)}")
    if fmt.color:
        rules.append(f"color:#{fmt.color}")
    if fmt.highlight:
        rules.append(f"background-color:{_highlight_to_css(fmt.highlight)}")
    if fmt.vertical_align == "superscript":
        rules.append("vertical-align:super;font-size:smaller")
    elif fmt.vertical_align == "subscript":
        rules.append("vertical-align:sub;font-size:smaller")
    return ";".join(rules)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tag(
    tag_name: str,
    classes: list[str],
    data_attrs: dict[str, str],
    inline_style: str,
    inner: str,
) -> str:
    parts = [f'class="{" ".join(classes)}"']
    if inline_style:
        parts.append(f'style="{inline_style}"')
    for k, v in data_attrs.items():
        parts.append(f'{k}="{html.escape(v, quote=True)}"')
    attrs_str = " ".join(parts)
    return f"<{tag_name} {attrs_str}>{inner}</{tag_name}>"


def _css_ident(style_id: str) -> str:
    """Convert a Word style ID to a safe CSS class name component."""
    return style_id.replace(" ", "-")


def _escape_text(text: str) -> str:
    """Escape text for HTML, preserving line breaks as <br>."""
    escaped = html.escape(text)
    return escaped.replace("\n", "<br>")


_HIGHLIGHT_COLOURS: dict[str, str] = {
    "black":     "#000000",
    "blue":      "#0000FF",
    "cyan":      "#00FFFF",
    "darkBlue":  "#000080",
    "darkCyan":  "#008080",
    "darkGray":  "#808080",
    "darkGreen": "#008000",
    "darkMagenta": "#800080",
    "darkRed":   "#800000",
    "darkYellow": "#808000",
    "green":     "#00FF00",
    "lightGray": "#C0C0C0",
    "magenta":   "#FF00FF",
    "none":      "transparent",
    "red":       "#FF0000",
    "white":     "#FFFFFF",
    "yellow":    "#FFFF00",
}


def _highlight_to_css(highlight: str) -> str:
    return _HIGHLIGHT_COLOURS.get(highlight, "yellow")
