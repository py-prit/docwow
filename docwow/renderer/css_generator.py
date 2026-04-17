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


def generate_css(doc: Document, page_view: bool = False) -> str:
    """Return a complete CSS string (without the <style> wrapper tags)."""
    parts: list[str] = [_BASE_CSS]
    parts.append(_document_rule(doc))
    for style in doc.styles:
        rule = _style_rule(style)
        if rule:
            parts.append(rule)
    if page_view:
        parts.append(_page_view_css(doc))
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
# Page-view CSS  (opt-in via page_view=True)
# ---------------------------------------------------------------------------

def _page_view_css(doc: Document) -> str:
    """Return @page and print CSS for page_view mode.

    Controls paper size and margins when the user prints or exports to PDF.
    Visual in-browser page separation is a planned future feature.
    """
    w = pt_to_css(doc.page_width_pt)
    h = pt_to_css(doc.page_height_pt)
    mt = pt_to_css(doc.margin_top_pt)
    mr = pt_to_css(doc.margin_right_pt)
    mb = pt_to_css(doc.margin_bottom_pt)
    ml = pt_to_css(doc.margin_left_pt)

    return f"""\
/* docwow — page view: print / PDF pagination */
@media print {{
  .dw-table, .dw-img {{
    page-break-inside: avoid;
  }}

  .dw-style-Heading1, .dw-style-Heading2, .dw-style-Heading3 {{
    page-break-after: avoid;
  }}

  @page {{
    size: {w} {h};
    margin: {mt} {mr} {mb} {ml};
  }}
}}"""


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
}

.dw-page-break {
  display: none;
}

.dw-page-only {
  display: none;
}

.dw-header, .dw-footer {
  max-width: var(--dw-page-width, 595.28pt);
  margin: 0 auto;
  padding: 4pt 72pt;
  font-size: 9pt;
  color: #555555;
  border-bottom: 1px solid #cccccc;
}

.dw-footer {
  border-top: 1px solid #cccccc;
  border-bottom: none;
}

.dw-field {
  color: #888888;
  font-style: italic;
}

/* Footnotes / endnotes */
.dw-footnote-ref, .dw-endnote-ref {
  font-size: 0.75em;
  vertical-align: super;
  line-height: 1;
  text-decoration: none;
  color: #1155cc;
  cursor: pointer;
}
.dw-footnote-ref:hover, .dw-endnote-ref:hover {
  text-decoration: underline;
}

.dw-footnotes, .dw-endnotes {
  max-width: var(--dw-page-width, 595.28pt);
  margin: 24pt auto 0;
  padding-top: 8pt;
  border-top: 1px solid #cccccc;
  font-size: 9pt;
}

.dw-footnotes-heading, .dw-endnotes-heading {
  font-size: 9pt;
  font-weight: bold;
  margin-bottom: 4pt;
}

.dw-fn, .dw-en {
  display: flex;
  gap: 6pt;
  margin-bottom: 4pt;
}

.dw-fn-marker, .dw-en-marker {
  flex-shrink: 0;
  font-size: 0.75em;
  vertical-align: super;
}

/* Table of Contents */
.dw-toc {
  margin: 12pt 0;
  padding: 0;
}

.dw-toc-title {
  font-size: 12pt;
  font-weight: bold;
  margin: 0 0 6pt 0;
}

.dw-toc-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.dw-toc-entry {
  margin: 2pt 0;
}

.dw-toc-level-1 { padding-left: 0; }
.dw-toc-level-2 { padding-left: 1.5em; }
.dw-toc-level-3 { padding-left: 3em; }
.dw-toc-level-4 { padding-left: 4.5em; }
.dw-toc-level-5 { padding-left: 6em; }
.dw-toc-level-6 { padding-left: 7.5em; }
.dw-toc-level-7 { padding-left: 9em; }
.dw-toc-level-8 { padding-left: 10.5em; }
.dw-toc-level-9 { padding-left: 12em; }

.dw-toc-link {
  color: inherit;
  text-decoration: none;
}

.dw-toc-link:hover {
  text-decoration: underline;
}

/* Comments */
.dw-comment-ref {
  color: #E65100;
  font-size: 0.75em;
  vertical-align: super;
  text-decoration: none;
}

.dw-comment-ref:hover {
  text-decoration: underline;
}

.dw-comments {
  margin-top: 2em;
  border-top: 2px solid #E65100;
  padding-top: 0.75em;
}

.dw-comment {
  margin: 0.5em 0;
  padding: 0.4em 0.6em;
  background: #FFF8E1;
  border-left: 3px solid #E65100;
  border-radius: 2px;
}

.dw-comment-marker {
  font-size: 0.75em;
  color: #E65100;
  vertical-align: super;
  font-weight: bold;
  margin-right: 0.4em;
}

.dw-comment-body {
  display: inline;
}"""
