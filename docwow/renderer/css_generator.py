"""
Generate the CSS <style> block for a rendered Document.

Two layers of CSS are produced:
  1. Base styles  — fixed rules for all docwow documents (.dw-document,
                    .dw-p, .dw-r, .dw-table, .dw-td, .dw-list, .dw-img …)
  2. Style classes — one CSS class per named Word style found in the document
                    (.dw-style-Normal, .dw-style-Heading1, …)

Visual rendering uses the style class + any inline style override on the
element.  Round-trip data lives in data-dw-* attributes, not in CSS.
"""

from __future__ import annotations

from docwow.models.document import Document
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.utils.units import pt_to_css


def generate_css(doc: Document) -> str:
    """Return a complete CSS string (without the <style> wrapper tags)."""
    parts: list[str] = [_BASE_CSS]
    parts.append(_document_rule(doc))
    for style in doc.styles:
        rule = _style_rule(style)
        if rule:
            parts.append(rule)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Document-level rule  (.dw-document)
# ---------------------------------------------------------------------------

def _document_rule(doc: Document) -> str:
    """Produce a CSS rule for .dw-document using the document's page geometry."""
    width_css = pt_to_css(doc.page_width_pt)
    padding_css = (
        f"{pt_to_css(doc.margin_top_pt)} "
        f"{pt_to_css(doc.margin_right_pt)} "
        f"{pt_to_css(doc.margin_bottom_pt)} "
        f"{pt_to_css(doc.margin_left_pt)}"
    )
    return (
        f".dw-document {{\n"
        f"  max-width:{width_css};\n"
        f"  padding:{padding_css};\n"
        f"}}"
    )


# ---------------------------------------------------------------------------
# Per-style rules
# ---------------------------------------------------------------------------

def _style_rule(style: Style) -> str:
    """Return a CSS rule for a single Word style, or '' if nothing to emit."""
    selector = f".dw-style-{_css_ident(style.style_id)}"
    declarations: list[str] = []

    if style.paragraph_fmt is not None:
        declarations.extend(_para_fmt_declarations(style.paragraph_fmt))

    if style.run_fmt is not None:
        declarations.extend(_run_fmt_declarations(style.run_fmt))

    if not declarations:
        return ""

    body = ";\n  ".join(declarations)
    return f"{selector} {{\n  {body};\n}}"


def _para_fmt_declarations(fmt: ParagraphFormatting) -> list[str]:
    decls: list[str] = []
    if fmt.alignment:
        decls.append(f"text-align:{fmt.alignment}")
    if fmt.indent_left_pt:
        decls.append(f"padding-left:{pt_to_css(fmt.indent_left_pt)}")
    if fmt.indent_right_pt:
        decls.append(f"padding-right:{pt_to_css(fmt.indent_right_pt)}")
    if fmt.indent_first_line_pt > 0:
        decls.append(f"text-indent:{pt_to_css(fmt.indent_first_line_pt)}")
    if fmt.space_before_pt:
        decls.append(f"margin-top:{pt_to_css(fmt.space_before_pt)}")
    if fmt.space_after_pt:
        decls.append(f"margin-bottom:{pt_to_css(fmt.space_after_pt)}")
    if fmt.line_spacing_pt is not None:
        decls.append(f"line-height:{pt_to_css(fmt.line_spacing_pt)}")
    return decls


def _run_fmt_declarations(fmt: RunFormatting) -> list[str]:
    decls: list[str] = []
    if fmt.bold:
        decls.append("font-weight:bold")
    if fmt.italic:
        decls.append("font-style:italic")
    decorations: list[str] = []
    if fmt.underline:
        decorations.append("underline")
    if fmt.strike:
        decorations.append("line-through")
    if decorations:
        decls.append(f"text-decoration:{' '.join(decorations)}")
    if fmt.font_name:
        decls.append(f"font-family:{fmt.font_name}")
    if fmt.font_size_pt is not None:
        decls.append(f"font-size:{pt_to_css(fmt.font_size_pt)}")
    if fmt.color:
        decls.append(f"color:#{fmt.color}")
    return decls


def _css_ident(style_id: str) -> str:
    return style_id.replace(" ", "-")


# ---------------------------------------------------------------------------
# Base CSS (fixed across all documents)
# ---------------------------------------------------------------------------

_BASE_CSS = """\
/* docwow — base styles */
*, *::before, *::after { box-sizing: border-box; }

.dw-document {
  margin: 0 auto;
  background: #ffffff;
  color: #000000;
  font-family: Calibri, 'Segoe UI', Arial, sans-serif;
  font-size: 11pt;
  line-height: 1.15;
  word-wrap: break-word;
}

.dw-p {
  margin: 0;
  padding: 0;
  min-height: 1em;
}

.dw-r {
  white-space: pre-wrap;
}

.dw-table {
  border-collapse: collapse;
  margin: 6pt 0;
}

.dw-tr { }

.dw-td {
  border: 1px solid #000000;
  vertical-align: top;
  padding: 4pt;
}

.dw-list {
  margin: 0;
  padding-left: 2em;
}

.dw-li {
  margin: 0;
  padding-left: 0.25em;
}

.dw-img {
  display: inline-block;
  max-width: 100%;
}"""
