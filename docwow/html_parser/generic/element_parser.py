"""DOM walker: HTML elements → Document model.

Converts arbitrary HTML to a :class:`~docwow.models.document.Document` using
best-effort heuristics.  Unsupported constructs emit
:class:`~docwow.DocwowConversionWarning` and are skipped.

Built incrementally across Phase 2 sub-features:
  feat/generic-block-elements   — h1-h6, p, div, blockquote, pre, hr, br  ← this PR
  feat/generic-inline-elements  — b/i/u/s/code/mark/sub/sup/span/a + CSS
  feat/generic-lists             — ul/ol/li
  feat/generic-tables            — table/tr/td/th
  feat/generic-images            — img
"""
from __future__ import annotations

import re
import urllib.request
from collections.abc import Iterator

import lxml.html

from docwow.html_parser.generic.css_resolver import CssResolver, parse_inline_style
from docwow.html_parser.generic.css_units import css_value_to_pt
from docwow.models.document import Document
from docwow.models.paragraph import PageBreak, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.warnings import warn as _warn

# ---------------------------------------------------------------------------
# Heading style definitions
# ---------------------------------------------------------------------------
# We define these explicitly so the DOCX works in all viewers (Pages,
# LibreOffice, Word) rather than relying on application-specific built-ins.

_HEADING_STYLE_DEFS: dict[str, Style] = {
    "Heading1": Style(
        style_id="Heading1", name="heading 1", style_type="paragraph",
        run_fmt=RunFormatting(bold=True, font_size_pt=20.0),
        paragraph_fmt=ParagraphFormatting(space_before_pt=12.0, space_after_pt=4.0),
    ),
    "Heading2": Style(
        style_id="Heading2", name="heading 2", style_type="paragraph",
        run_fmt=RunFormatting(bold=True, font_size_pt=16.0),
        paragraph_fmt=ParagraphFormatting(space_before_pt=10.0, space_after_pt=2.0),
    ),
    "Heading3": Style(
        style_id="Heading3", name="heading 3", style_type="paragraph",
        run_fmt=RunFormatting(bold=True, font_size_pt=14.0),
        paragraph_fmt=ParagraphFormatting(space_before_pt=8.0, space_after_pt=2.0),
    ),
    "Heading4": Style(
        style_id="Heading4", name="heading 4", style_type="paragraph",
        run_fmt=RunFormatting(bold=True, font_size_pt=13.0),
        paragraph_fmt=ParagraphFormatting(space_before_pt=6.0, space_after_pt=2.0),
    ),
    "Heading5": Style(
        style_id="Heading5", name="heading 5", style_type="paragraph",
        run_fmt=RunFormatting(bold=True, font_size_pt=12.0),
        paragraph_fmt=ParagraphFormatting(space_before_pt=4.0, space_after_pt=0.0),
    ),
    "Heading6": Style(
        style_id="Heading6", name="heading 6", style_type="paragraph",
        run_fmt=RunFormatting(bold=True, italic=True, font_size_pt=11.0),
        paragraph_fmt=ParagraphFormatting(space_before_pt=2.0, space_after_pt=0.0),
    ),
}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HEADING_STYLE: dict[str, str] = {
    "h1": "Heading1", "h2": "Heading2", "h3": "Heading3",
    "h4": "Heading4", "h5": "Heading5", "h6": "Heading6",
}

# Tags that produce block-level body elements
_BLOCK_TAGS = frozenset({
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "div", "section", "article", "main", "aside",
    "blockquote", "pre", "hr",
    "ul", "ol",         # lists — handled in feat/generic-lists
    "table",            # tables — handled in feat/generic-tables
    "figure", "figcaption", "address", "details", "summary",
    "header", "footer", "nav",
})

# Tags whose children we recurse into without emitting a paragraph themselves
_TRANSPARENT_TAGS = frozenset({
    "section", "article", "main", "aside",
    "header", "footer", "nav", "figure", "details",
})

# Tags we silently skip (no warning — these are structural/non-content)
_SILENT_SKIP_TAGS = frozenset({
    "script", "style", "noscript", "template",
    "head", "meta", "link", "title", "base",
})

# Tags that produce warnings (no Word equivalent)
_UNSUPPORTED_TAGS = frozenset({
    "iframe", "video", "audio", "canvas", "object", "embed",
    "svg", "math", "form", "input", "button", "select", "textarea",
})

_DEFAULT_PAGE_WIDTH_PT = 595.28
_DEFAULT_MARGINS_PT = 72.0
_BLOCKQUOTE_INDENT_PT = 36.0

# Word built-in style IDs that must NOT be defined in styles.xml.
# Defining them with an empty body overrides Word's own formatting
# (bold fonts, spacing, etc.) with a blank style.  Omitting them
# lets Word apply its built-in definitions automatically.
_BUILTIN_WORD_STYLES = frozenset({
    "Normal", "DefaultParagraphFont",
    "Heading1", "Heading2", "Heading3", "Heading4",
    "Heading5", "Heading6", "Heading7", "Heading8", "Heading9",
    "Title", "Subtitle", "Caption",
    "ListParagraph", "Quote", "IntenseQuote",
    "TableGrid", "TableNormal",
})


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

class ElementParser:
    """Walks the HTML DOM and builds a :class:`~docwow.models.document.Document`."""

    def __init__(self, fetch_images: bool = False, fetch_external_css: bool = False) -> None:
        self.fetch_images = fetch_images
        self.fetch_external_css = fetch_external_css
        self._warned_tags: set[str] = set()

    def parse(self, html: str) -> Document:
        """Parse an HTML string into a :class:`~docwow.models.document.Document`."""
        root = lxml.html.document_fromstring(html)

        # Collect CSS from <style> blocks and optionally external stylesheets
        css_blocks = _extract_style_blocks(root)
        if self.fetch_external_css:
            css_blocks.extend(_fetch_external_css(root))
        else:
            if _has_external_css(root):
                _warn(
                    "Found <link rel=\"stylesheet\"> but fetch_external_css=False "
                    "— external styles ignored. Pass fetch_external_css=True to apply them."
                )

        resolver = CssResolver(css_blocks)

        body_el = root.find(".//body")
        if body_el is None:
            body_el = root

        body_elements = list(self._walk(body_el, resolver, blockquote_depth=0))

        # Build styles tuple: use explicit heading definitions for h1-h6
        # (so all DOCX viewers show correct sizes/weights), and minimal Style
        # objects for any other custom style IDs encountered.
        style_ids: set[str] = set()
        for el in body_elements:
            if isinstance(el, Paragraph) and el.formatting.style_id:
                style_ids.add(el.formatting.style_id)

        styles_list: list[Style] = []
        for sid in sorted(style_ids):
            if sid in _HEADING_STYLE_DEFS:
                styles_list.append(_HEADING_STYLE_DEFS[sid])
            elif sid not in _BUILTIN_WORD_STYLES:
                styles_list.append(Style(style_id=sid, name=sid, style_type="paragraph"))
        styles = tuple(styles_list)

        return Document(
            body=tuple(body_elements),
            styles=styles,
            numbering=(),
        )

    # -----------------------------------------------------------------------
    # DOM walking
    # -----------------------------------------------------------------------

    def _walk(
        self,
        el,
        resolver: CssResolver,
        blockquote_depth: int,
    ) -> Iterator:
        """Recursively yield body elements from *el*'s children."""
        for child in el:
            tag = child.tag
            if not isinstance(tag, str):
                continue  # lxml comments, PIs, etc.

            tag = tag.lower()

            if tag in _SILENT_SKIP_TAGS:
                continue

            if tag in _UNSUPPORTED_TAGS:
                self._warn_once(
                    tag,
                    f"<{tag}> has no Word equivalent — element skipped.",
                )
                continue

            if tag in _TRANSPARENT_TAGS:
                yield from self._walk(child, resolver, blockquote_depth)
                continue

            if tag in _HEADING_STYLE:
                yield self._parse_heading(child, tag, resolver)
                continue

            if tag == "p":
                para = self._parse_paragraph(child, resolver, blockquote_depth)
                if para is not None:
                    yield para
                continue

            if tag == "div":
                yield from self._parse_div(child, resolver, blockquote_depth)
                continue

            if tag == "blockquote":
                yield from self._walk(child, resolver, blockquote_depth + 1)
                continue

            if tag == "pre":
                yield self._parse_pre(child, resolver)
                continue

            if tag == "hr":
                yield self._parse_hr(resolver)
                continue

            # Lists and tables — stubs until their sub-features land
            if tag in ("ul", "ol"):
                _warn(
                    f"<{tag}> list parsing is not yet supported — "
                    "text content will be extracted as plain paragraphs."
                )
                yield from self._walk(child, resolver, blockquote_depth)
                continue

            if tag == "li":
                para = self._parse_paragraph(child, resolver, blockquote_depth)
                if para is not None:
                    yield para
                continue

            if tag == "table":
                _warn(
                    "<table> parsing is not yet supported — element skipped."
                )
                continue

            # img — stub until feat/generic-images
            if tag == "img":
                src = child.get("src", "")
                if src.startswith("data:"):
                    _warn("<img> (data URI) is not yet supported — image skipped.")
                else:
                    if self.fetch_images:
                        _warn("<img> fetching is not yet supported — image skipped.")
                    else:
                        _warn(
                            f"Found <img src=\"{src[:60]}...\"> but fetch_images=False "
                            "— image skipped. Pass fetch_images=True to download remote images."
                        )
                continue

            # Unknown block-ish elements: recurse to preserve content
            if _has_block_children(child):
                yield from self._walk(child, resolver, blockquote_depth)
            else:
                para = self._parse_paragraph(child, resolver, blockquote_depth)
                if para is not None:
                    yield para

    # -----------------------------------------------------------------------
    # Element-specific parsers
    # -----------------------------------------------------------------------

    def _parse_heading(self, el, tag: str, resolver: CssResolver) -> Paragraph:
        style_id = _HEADING_STYLE[tag]
        fmt = self._para_fmt_from_css(resolver.resolve(el), style_id=style_id)
        runs = self._runs_from_element(el, resolver)
        return Paragraph(runs=tuple(runs), formatting=fmt)

    def _parse_paragraph(
        self, el, resolver: CssResolver, blockquote_depth: int
    ) -> Paragraph | None:
        runs = self._runs_from_element(el, resolver)
        if not runs:
            return None
        props = resolver.resolve(el)
        extra_indent = blockquote_depth * _BLOCKQUOTE_INDENT_PT
        fmt = self._para_fmt_from_css(props, extra_indent=extra_indent)
        return Paragraph(runs=tuple(runs), formatting=fmt)

    def _parse_div(
        self, el, resolver: CssResolver, blockquote_depth: int
    ) -> Iterator:
        """A <div> is a transparent container if it has block children,
        otherwise a paragraph."""
        if _has_block_children(el):
            # Discard loose text nodes in mixed-content divs (per plan)
            yield from self._walk(el, resolver, blockquote_depth)
        else:
            para = self._parse_paragraph(el, resolver, blockquote_depth)
            if para is not None:
                yield para

    def _parse_pre(self, el, resolver: CssResolver) -> Paragraph:
        """<pre> — monospace paragraph preserving whitespace."""
        text = _extract_text_pre(el)
        run = TextRun(
            text=text,
            formatting=RunFormatting(font_name="Courier New"),
        )
        props = resolver.resolve(el)
        fmt = self._para_fmt_from_css(props)
        return Paragraph(runs=(run,), formatting=fmt)

    def _parse_hr(self, resolver: CssResolver) -> Paragraph:
        """<hr> — empty paragraph as a visual separator."""
        return Paragraph(
            runs=(TextRun(text=""),),
            formatting=ParagraphFormatting(),
        )

    # -----------------------------------------------------------------------
    # Run building (sub-feature 2: plain text only)
    # Sub-feature 3 (inline elements) will replace _runs_from_element with
    # a full inline content walker.
    # -----------------------------------------------------------------------

    def _runs_from_element(self, el, resolver: CssResolver) -> list[TextRun]:
        """Extract runs from a block element.

        Sub-feature 2: plain text only — one run per element, no inline formatting.
        Sub-feature 3 will replace this with a proper inline content walker.
        """
        text = _extract_text_block(el)
        if not text:
            return []
        return [TextRun(text=text, formatting=RunFormatting())]

    # -----------------------------------------------------------------------
    # CSS → ParagraphFormatting
    # -----------------------------------------------------------------------

    def _para_fmt_from_css(
        self,
        props: dict[str, str],
        style_id: str | None = None,
        extra_indent: float = 0.0,
    ) -> ParagraphFormatting:
        alignment = _css_alignment(props.get("text-align"))
        indent_left = (
            css_value_to_pt(props["margin-left"]) or 0.0
            if "margin-left" in props else 0.0
        ) + (
            css_value_to_pt(props["padding-left"]) or 0.0
            if "padding-left" in props else 0.0
        ) + extra_indent
        indent_right = (
            css_value_to_pt(props["margin-right"]) or 0.0
            if "margin-right" in props else 0.0
        ) + (
            css_value_to_pt(props["padding-right"]) or 0.0
            if "padding-right" in props else 0.0
        )
        space_before = css_value_to_pt(props["margin-top"]) if "margin-top" in props else 0.0
        space_after = css_value_to_pt(props["margin-bottom"]) if "margin-bottom" in props else 0.0
        shading = _css_color_to_hex(props.get("background-color"))

        return ParagraphFormatting(
            style_id=style_id,
            alignment=alignment,
            indent_left_pt=indent_left or 0.0,
            indent_right_pt=indent_right or 0.0,
            space_before_pt=space_before or 0.0,
            space_after_pt=space_after or 0.0,
            shading=shading,
        )

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _warn_once(self, key: str, message: str) -> None:
        if key not in self._warned_tags:
            self._warned_tags.add(key)
            _warn(message)


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _extract_text_block(el) -> str:
    """Extract normalised text content from a block element.

    Handles <br> as \\n.  Collapses whitespace (multiple spaces → one).
    """
    parts: list[str] = []
    _collect_text(el, parts)
    text = "".join(parts)
    # Collapse runs of whitespace but preserve intentional newlines
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def _extract_text_pre(el) -> str:
    """Extract text from <pre> preserving all whitespace."""
    parts: list[str] = []
    _collect_text(el, parts)
    return "".join(parts)


def _collect_text(el, parts: list[str]) -> None:
    """Recursively collect text, converting <br> to \\n."""
    tag = el.tag if isinstance(el.tag, str) else ""
    if tag.lower() == "br":
        parts.append("\n")
    if el.text:
        parts.append(el.text)
    for child in el:
        _collect_text(child, parts)
    if el.tail:
        parts.append(el.tail)


# ---------------------------------------------------------------------------
# CSS extraction helpers
# ---------------------------------------------------------------------------

def _extract_style_blocks(root) -> list[str]:
    """Collect text from all <style> tags in the document."""
    blocks = []
    for el in root.iter("style"):
        if el.text:
            blocks.append(el.text)
    return blocks


def _has_external_css(root) -> bool:
    for el in root.iter("link"):
        if (el.get("rel") or "").lower() == "stylesheet" and el.get("href"):
            return True
    return False


def _fetch_external_css(root) -> list[str]:
    """Download external stylesheets. Returns CSS strings."""
    blocks = []
    for el in root.iter("link"):
        if (el.get("rel") or "").lower() != "stylesheet":
            continue
        href = el.get("href", "")
        if not href or not href.startswith(("http://", "https://")):
            continue
        try:
            with urllib.request.urlopen(href, timeout=10) as resp:
                blocks.append(resp.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            _warn(f"Failed to fetch external CSS from {href!r}: {exc} — stylesheet ignored.")
    return blocks


# ---------------------------------------------------------------------------
# DOM helpers
# ---------------------------------------------------------------------------

def _has_block_children(el) -> bool:
    """Return True if *el* has any direct block-level children."""
    for child in el:
        if isinstance(child.tag, str) and child.tag.lower() in _BLOCK_TAGS:
            return True
    return False


# ---------------------------------------------------------------------------
# CSS value helpers
# ---------------------------------------------------------------------------

def _css_alignment(value: str | None) -> str | None:
    if not value:
        return None
    mapping = {
        "left": "left", "center": "center", "right": "right",
        "justify": "justify", "start": "left", "end": "right",
    }
    return mapping.get(value.strip().lower())


# Common CSS named colors → 6-digit hex RGB
_NAMED_COLORS: dict[str, str] = {
    "black": "000000", "white": "FFFFFF", "red": "FF0000",
    "green": "008000", "blue": "0000FF", "yellow": "FFFF00",
    "cyan": "00FFFF", "aqua": "00FFFF", "magenta": "FF00FF",
    "fuchsia": "FF00FF", "orange": "FFA500", "purple": "800080",
    "brown": "A52A2A", "gray": "808080", "grey": "808080",
    "silver": "C0C0C0", "lime": "00FF00", "navy": "000080",
    "olive": "808000", "teal": "008080", "maroon": "800000",
    "pink": "FFC0CB", "coral": "FF7F50", "salmon": "FA8072",
    "gold": "FFD700", "khaki": "F0E68C", "indigo": "4B0082",
    "violet": "EE82EE", "turquoise": "40E0D0", "tan": "D2B48C",
}


def _css_color_to_hex(value: str | None) -> str | None:
    """Convert a CSS color value to a 6-digit uppercase hex string (no #).

    Returns None for transparent, inherit, or unrecognised values.
    """
    if not value:
        return None
    v = value.strip().lower()
    if v in ("transparent", "inherit", "initial", "unset", "currentcolor"):
        return None

    # Named color
    if v in _NAMED_COLORS:
        return _NAMED_COLORS[v]

    # #RGB or #RRGGBB
    if v.startswith("#"):
        hex_val = v[1:]
        if len(hex_val) == 3:
            hex_val = "".join(c * 2 for c in hex_val)
        if len(hex_val) == 6:
            return hex_val.upper()
        return None

    # rgb(r, g, b)
    m = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', v)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{r:02X}{g:02X}{b:02X}"

    # rgba(r, g, b, a) — ignore alpha
    m = re.match(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)', v)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{r:02X}{g:02X}{b:02X}"

    return None
