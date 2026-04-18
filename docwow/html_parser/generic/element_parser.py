"""DOM walker: HTML elements → Document model.

Converts arbitrary HTML to a :class:`~docwow.models.document.Document` using
best-effort heuristics.  Unsupported constructs emit
:class:`~docwow.DocwowConversionWarning` and are skipped.

Built incrementally across Phase 2 sub-features:
  feat/generic-block-elements   — h1-h6, p, div, blockquote, pre, hr, br
  feat/generic-inline-elements  — b/i/u/s/code/mark/sub/sup/span/a + CSS
  feat/generic-lists             — ul/ol/li, nesting
  feat/generic-tables            — table/tr/td/th, colspan/rowspan  ← this PR
  feat/generic-images            — img
"""
from __future__ import annotations

import dataclasses
import re
import urllib.request
from collections.abc import Iterator

import lxml.html

from docwow.html_parser.generic.css_resolver import CssResolver, parse_inline_style
from docwow.html_parser.generic.css_units import css_value_to_pt
from docwow.models.document import Document
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import Hyperlink, PageBreak, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.models.table import BorderDef, Table, TableBorders, TableCell, TableRow
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
        self._next_num_id: int = 0
        self._numbering_defs: list[NumberingDefinition] = []

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
            numbering=tuple(self._numbering_defs),
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

            if tag in ("ul", "ol"):
                yield from self._parse_list(child, resolver, blockquote_depth)
                continue

            if tag == "li":
                # Orphan <li> outside a list — treat as plain paragraph
                para = self._parse_paragraph(child, resolver, blockquote_depth)
                if para is not None:
                    yield para
                continue

            if tag == "table":
                yield from self._parse_table(child, resolver, blockquote_depth)
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
        # Skip paragraphs whose only content is whitespace
        has_content = any(
            (r.text.strip() if isinstance(r, TextRun) else True) for r in runs
        )
        if not has_content:
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

    def _parse_list(
        self,
        el,
        resolver: CssResolver,
        blockquote_depth: int,
        depth: int = 0,
    ) -> Iterator[Paragraph]:
        """Parse a <ul> or <ol> into list-item Paragraphs.

        Every list element gets its own NumberingDefinition so that:
        - each list has the correct format (bullet vs decimal)
        - nested counters restart independently
        - mixed nesting (ul inside ol) works correctly

        Items sit at *depth* within their own definition for correct indentation.
        """
        self._next_num_id += 1
        num_id = str(self._next_num_id)
        tag = el.tag.lower() if isinstance(el.tag, str) else "ul"
        num_fmt = _resolve_list_num_fmt(el, tag, resolver)
        nd = _make_numbering_def(num_id, tag, depth, num_fmt=num_fmt)
        self._numbering_defs.append(nd)

        for child in el:
            child_tag = child.tag if isinstance(child.tag, str) else ""
            child_tag = child_tag.lower()

            if child_tag != "li":
                continue

            runs = self._runs_from_element(child, resolver)
            has_content = any(
                (r.text.strip() if isinstance(r, TextRun) else True) for r in runs
            )
            list_info = ListInfo(num_id=num_id, level=depth)
            if runs and has_content:
                fmt = self._para_fmt_from_css(resolver.resolve(child))
                yield Paragraph(runs=tuple(runs), formatting=fmt, list_info=list_info)
            else:
                yield Paragraph(
                    runs=(TextRun(text=""),),
                    formatting=ParagraphFormatting(),
                    list_info=list_info,
                )

            # Recurse into nested lists inside this <li>
            for grandchild in child:
                gc_tag = grandchild.tag if isinstance(grandchild.tag, str) else ""
                gc_tag = gc_tag.lower()
                if gc_tag in ("ul", "ol"):
                    yield from self._parse_list(
                        grandchild, resolver, blockquote_depth, depth=depth + 1,
                    )

    # -----------------------------------------------------------------------
    # Table parsing
    # -----------------------------------------------------------------------

    def _parse_table(
        self,
        table_el,
        resolver: CssResolver,
        blockquote_depth: int,
    ) -> Iterator[Table]:
        """Parse a <table> element into a :class:`~docwow.models.table.Table`.

        Handles colspan and rowspan by building a logical grid first, then
        emitting OOXML-style v_merge_start / v_merge_continue cells.
        """
        tr_els = _collect_tr_elements(table_el)
        if not tr_els:
            return

        grid, num_rows, max_col = _build_table_grid(tr_els)
        if not grid or max_col == 0:
            return

        table_css = resolver.resolve(table_el)
        table_width_pt = (
            css_value_to_pt(table_css["width"]) if "width" in table_css else None
        )
        # Default to full text width so tables don't render at minimum content width
        if table_width_pt is None:
            table_width_pt = _DEFAULT_PAGE_WIDTH_PT - 2.0 * _DEFAULT_MARGINS_PT

        col_widths = _extract_col_widths(table_el, resolver, max_col)
        # If no explicit column widths, distribute evenly across columns
        if not col_widths and max_col > 0:
            col_widths = [table_width_pt / max_col] * max_col

        table_borders = _parse_table_borders(table_el, table_css)

        rows = []
        for row_idx in range(num_rows):
            cells = []
            col = 0
            while col < max_col:
                if (row_idx, col) not in grid:
                    col += 1
                    continue

                cell_el, cell_tag, colspan, rowspan, start_row, start_col = grid[
                    (row_idx, col)
                ]

                if row_idx == start_row and col == start_col:
                    # Origin cell — emit with full content
                    paras = self._parse_cell_content(
                        cell_el, resolver, blockquote_depth, is_header=cell_tag == "th"
                    )
                    cell_css = resolver.resolve(cell_el)
                    shading = _css_color_to_hex(cell_css.get("background-color"))
                    cell_borders = _parse_cell_borders(cell_css)
                    cells.append(
                        TableCell(
                            paragraphs=tuple(paras),
                            col_span=colspan,
                            row_span=rowspan,
                            v_merge_start=rowspan > 1,
                            shading=shading,
                            borders=cell_borders,
                        )
                    )
                    col += colspan

                elif col == start_col:
                    # Continuation row of a rowspan — emit empty vMerge placeholder
                    cells.append(
                        TableCell(
                            paragraphs=(
                                Paragraph(
                                    runs=(TextRun(text=""),),
                                    formatting=ParagraphFormatting(),
                                ),
                            ),
                            col_span=colspan,
                            v_merge_continue=True,
                        )
                    )
                    col += colspan

                else:
                    # Colspan continuation slot — already covered by origin/vMerge cell
                    col += 1

            if cells:
                rows.append(TableRow(cells=tuple(cells)))

        if rows:
            yield Table(
                rows=tuple(rows),
                col_widths_pt=tuple(col_widths),
                width_pt=table_width_pt,
                style_id="TableGrid",
                borders=table_borders,
            )

    def _parse_cell_content(
        self,
        cell_el,
        resolver: CssResolver,
        blockquote_depth: int,
        is_header: bool,
    ) -> list[Paragraph]:
        """Parse the content of a <td>/<th> into Paragraph objects."""
        if _has_block_children(cell_el):
            paras = []
            for el in self._walk(cell_el, resolver, blockquote_depth):
                if isinstance(el, Paragraph):
                    paras.append(el)
                elif isinstance(el, Table):
                    self._warn_once(
                        "nested-table",
                        "Nested <table> inside <td>/<th> is not supported — inner table skipped.",
                    )
        else:
            para = self._parse_paragraph(cell_el, resolver, blockquote_depth)
            paras = [para] if para else []

        if is_header:
            paras = [_bold_paragraph(p) for p in paras]

        if not paras:
            paras = [
                Paragraph(
                    runs=(TextRun(text=""),),
                    formatting=ParagraphFormatting(),
                )
            ]

        return paras

    # -----------------------------------------------------------------------
    # Run building — inline content walker
    # -----------------------------------------------------------------------

    def _runs_from_element(
        self, el, resolver: CssResolver
    ) -> list[TextRun | Hyperlink]:
        """Walk the inline content of a block element, yielding formatted runs."""
        out: list[TextRun | Hyperlink] = []
        self._walk_inline(el, resolver, RunFormatting(), out)
        return out

    def _walk_inline(
        self,
        el,
        resolver: CssResolver,
        inherited_fmt: RunFormatting,
        out: list[TextRun | Hyperlink],
    ) -> None:
        """Recursively collect inline runs from *el*, accumulating formatting."""
        if el.text:
            text = _normalize_inline_text(el.text)
            if text:
                out.append(TextRun(text=text, formatting=inherited_fmt))

        for child in el:
            child_tag = child.tag if isinstance(child.tag, str) else ""
            child_tag = child_tag.lower()

            if child_tag in _SILENT_SKIP_TAGS:
                pass

            elif child_tag == "br":
                out.append(TextRun(text="\n", formatting=inherited_fmt))

            elif child_tag == "img":
                pass  # handled in feat/generic-images

            elif child_tag in _BLOCK_TAGS:
                if child_tag not in ("ul", "ol"):
                    # Recurse non-list block elements as inline
                    child_fmt = _apply_tag_fmt(child_tag, inherited_fmt)
                    child_fmt = _apply_css_run_fmt(resolver.resolve(child), child_fmt)
                    self._walk_inline(child, resolver, child_fmt, out)
                # ul/ol inside inline content are skipped; tail text still emitted below

            elif child_tag == "a":
                href = child.get("href", "").strip()
                child_fmt = _apply_tag_fmt(child_tag, inherited_fmt)
                child_fmt = _apply_css_run_fmt(resolver.resolve(child), child_fmt)
                inner: list[TextRun | Hyperlink] = []
                self._walk_inline(child, resolver, child_fmt, inner)
                text_runs = tuple(r for r in inner if isinstance(r, TextRun))
                if href and text_runs:
                    out.append(Hyperlink(url=href, runs=text_runs))
                else:
                    out.extend(inner)

            else:
                child_fmt = _apply_tag_fmt(child_tag, inherited_fmt)
                child_fmt = _apply_css_run_fmt(resolver.resolve(child), child_fmt)
                self._walk_inline(child, resolver, child_fmt, out)

            # Tail text belongs to the *parent's* formatting, not the child's
            if child.tail:
                text = _normalize_inline_text(child.tail)
                if text:
                    out.append(TextRun(text=text, formatting=inherited_fmt))

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

def _normalize_inline_text(text: str) -> str:
    """Collapse runs of whitespace to a single space (HTML inline rules)."""
    return re.sub(r'[ \t\r\n]+', ' ', text)


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
# List helpers
# ---------------------------------------------------------------------------

# CSS list-style-type → Word num_fmt
_LIST_STYLE_TYPE_MAP: dict[str, str] = {
    "disc": "bullet", "circle": "bullet", "square": "bullet",
    "decimal": "decimal", "decimal-leading-zero": "decimal",
    "lower-alpha": "lowerLetter", "lower-latin": "lowerLetter",
    "upper-alpha": "upperLetter", "upper-latin": "upperLetter",
    "lower-roman": "lowerRoman", "upper-roman": "upperRoman",
    "none": "none",
}

_DEFAULT_INDENT_PT = 36.0   # 0.5 inch per level
_DEFAULT_HANGING_PT = 18.0  # bullet/number protrudes 0.25 inch

# Bullet characters cycling across nesting levels — matches Word's default bullet list
_BULLET_CHARS = ["\u2022", "\u25e6", "\u25aa"]  # •  ◦  ▪


# <ol type="…"> attribute → Word num_fmt
_OL_TYPE_MAP: dict[str, str] = {
    "1": "decimal",
    "a": "lowerLetter", "A": "upperLetter",
    "i": "lowerRoman",  "I": "upperRoman",
}


def _resolve_list_num_fmt(el, tag: str, resolver: CssResolver) -> str:
    """Determine Word num_fmt from CSS list-style-type and <ol type> attribute."""
    props = resolver.resolve(el)
    lst = props.get("list-style-type", "").strip().lower()
    if lst and lst in _LIST_STYLE_TYPE_MAP:
        return _LIST_STYLE_TYPE_MAP[lst]
    # <ol type="a|A|i|I|1">
    if tag == "ol":
        ol_type = el.get("type", "")
        if ol_type in _OL_TYPE_MAP:
            return _OL_TYPE_MAP[ol_type]
        return "decimal"
    return "bullet"


def _make_numbering_def(
    num_id: str, tag: str, depth: int = 0, num_fmt: str | None = None
) -> NumberingDefinition:
    """Build a NumberingDefinition for a <ul> or <ol> element."""
    if num_fmt is None:
        num_fmt = "bullet" if tag == "ul" else "decimal"
    is_bullet = num_fmt == "bullet"
    levels = tuple(
        ListLevel(
            level=i,
            num_fmt=num_fmt,
            start_value=1,
            text_template=_BULLET_CHARS[i % len(_BULLET_CHARS)] if is_bullet else f"%{i + 1}.",
            indent_pt=_DEFAULT_INDENT_PT * (i + 1),
            hanging_pt=_DEFAULT_HANGING_PT,
        )
        for i in range(9)
    )
    return NumberingDefinition(abstract_num_id=num_id, levels=levels)


# ---------------------------------------------------------------------------
# Inline formatting helpers
# ---------------------------------------------------------------------------

# HTML tags that imply specific RunFormatting overrides
_TAG_FMT_BOLD = frozenset({"b", "strong"})
_TAG_FMT_ITALIC = frozenset({"i", "em", "cite", "dfn", "var"})
_TAG_FMT_UNDERLINE = frozenset({"u", "ins"})
_TAG_FMT_STRIKE = frozenset({"s", "del", "strike"})
_TAG_FMT_CODE = frozenset({"code", "kbd", "samp", "tt"})
_TAG_FMT_MARK = frozenset({"mark"})
_TAG_FMT_SUB = frozenset({"sub"})
_TAG_FMT_SUP = frozenset({"sup"})
_TAG_FMT_SMALL_CAPS = frozenset({"abbr", "acronym"})


def _apply_tag_fmt(tag: str, fmt: RunFormatting) -> RunFormatting:
    """Return a new RunFormatting with overrides implied by *tag*."""
    if tag in _TAG_FMT_BOLD:
        return dataclasses.replace(fmt, bold=True)
    if tag in _TAG_FMT_ITALIC:
        return dataclasses.replace(fmt, italic=True)
    if tag in _TAG_FMT_UNDERLINE:
        return dataclasses.replace(fmt, underline=True)
    if tag in _TAG_FMT_STRIKE:
        return dataclasses.replace(fmt, strike=True)
    if tag in _TAG_FMT_CODE:
        return dataclasses.replace(fmt, font_name="Courier New")
    if tag in _TAG_FMT_MARK:
        return dataclasses.replace(fmt, highlight="yellow")
    if tag in _TAG_FMT_SUB:
        return dataclasses.replace(fmt, vertical_align="subscript")
    if tag in _TAG_FMT_SUP:
        return dataclasses.replace(fmt, vertical_align="superscript")
    if tag in _TAG_FMT_SMALL_CAPS:
        return dataclasses.replace(fmt, small_caps=True)
    return fmt


def _apply_css_run_fmt(props: dict[str, str], fmt: RunFormatting) -> RunFormatting:
    """Apply CSS properties to *fmt*, returning a new RunFormatting."""
    kwargs: dict = {}

    fw = props.get("font-weight", "").strip().lower()
    if fw in ("bold", "bolder") or (fw.isdigit() and int(fw) >= 600):
        kwargs["bold"] = True
    elif fw in ("normal", "lighter") or (fw.isdigit() and int(fw) < 600):
        kwargs["bold"] = False

    fs = props.get("font-style", "").strip().lower()
    if fs == "italic" or fs == "oblique":
        kwargs["italic"] = True
    elif fs == "normal":
        kwargs["italic"] = False

    td = props.get("text-decoration", "").strip().lower()
    if "underline" in td:
        kwargs["underline"] = True
    if "line-through" in td:
        kwargs["strike"] = True

    fv = props.get("font-variant", "").strip().lower()
    if "small-caps" in fv:
        kwargs["small_caps"] = True

    tt = props.get("text-transform", "").strip().lower()
    if tt == "uppercase":
        kwargs["all_caps"] = True

    va = props.get("vertical-align", "").strip().lower()
    if va == "super":
        kwargs["vertical_align"] = "superscript"
    elif va == "sub":
        kwargs["vertical_align"] = "subscript"

    ff = props.get("font-family", "").strip()
    if ff:
        # Take the first family name, unquote and strip
        first = ff.split(",")[0].strip().strip("'\"")
        if first:
            kwargs["font_name"] = first

    fsize = props.get("font-size", "").strip()
    if fsize:
        pt = css_value_to_pt(fsize)
        if pt is not None and pt > 0:
            kwargs["font_size_pt"] = pt

    color = props.get("color", "").strip()
    if color:
        hex_color = _css_color_to_hex(color)
        if hex_color is not None:
            kwargs["color"] = hex_color

    bg = props.get("background-color", "").strip()
    if bg:
        hl = _css_bg_to_highlight(bg)
        if hl is not None:
            kwargs["highlight"] = hl

    if not kwargs:
        return fmt
    return dataclasses.replace(fmt, **kwargs)


# Approximate CSS background colors to the 15 Word highlight color names.
# Word's palette: black, blue, cyan, darkBlue, darkCyan, darkGreen,
# darkMagenta, darkRed, darkYellow, gray, green, lightGray, magenta, red, yellow
_HIGHLIGHT_MAP: dict[str, str] = {
    "yellow": "yellow", "ffff00": "yellow",
    "green": "green", "00ff00": "green", "008000": "green",
    "cyan": "cyan", "00ffff": "cyan",
    "magenta": "magenta", "ff00ff": "magenta",
    "red": "red", "ff0000": "red",
    "blue": "blue", "0000ff": "blue",
    "darkblue": "darkBlue", "000080": "darkBlue",
    "darkcyan": "darkCyan", "008080": "darkCyan",
    "darkgreen": "darkGreen",
    "darkmagenta": "darkMagenta", "800080": "darkMagenta",
    "darkred": "darkRed", "800000": "darkRed",
    "darkyellow": "darkYellow", "808000": "darkYellow",
    "gray": "gray", "808080": "gray", "grey": "gray",
    "silver": "lightGray", "c0c0c0": "lightGray",
    "black": "black", "000000": "black",
    "white": "white", "ffffff": "white",
}


def _css_bg_to_highlight(value: str) -> str | None:
    """Map a CSS background-color to a Word highlight name, or None if no match."""
    hex_val = _css_color_to_hex(value)
    if hex_val is None:
        v = value.strip().lower()
        return _HIGHLIGHT_MAP.get(v)
    return _HIGHLIGHT_MAP.get(hex_val.lower())


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


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def _collect_tr_elements(table_el) -> list:
    """Collect <tr> elements from a <table>, handling thead/tbody/tfoot sections."""
    tr_els = []
    for child in table_el:
        if not isinstance(child.tag, str):
            continue
        tag = child.tag.lower()
        if tag == "tr":
            tr_els.append(child)
        elif tag in ("thead", "tbody", "tfoot"):
            for grandchild in child:
                if (
                    isinstance(grandchild.tag, str)
                    and grandchild.tag.lower() == "tr"
                ):
                    tr_els.append(grandchild)
    return tr_els


def _build_table_grid(
    tr_els: list,
) -> tuple[dict[tuple[int, int], tuple], int, int]:
    """Build a (row, col) → cell-info grid from <tr>/<td>/<th> elements.

    HTML rowspan/colspan are expanded so every occupied slot maps back to the
    cell element that owns it plus its origin coordinates.

    Returns ``(grid, num_rows, max_col)``.
    """
    grid: dict[tuple[int, int], tuple] = {}

    for row_idx, tr_el in enumerate(tr_els):
        col_idx = 0
        for cell_el in tr_el:
            if not isinstance(cell_el.tag, str):
                continue
            cell_tag = cell_el.tag.lower()
            if cell_tag not in ("td", "th"):
                continue

            # Skip slots already claimed by a rowspan from a previous row
            while (row_idx, col_idx) in grid:
                col_idx += 1

            try:
                colspan = max(1, int(cell_el.get("colspan") or "1"))
                rowspan = max(1, int(cell_el.get("rowspan") or "1"))
            except (ValueError, TypeError):
                colspan = rowspan = 1

            for r in range(row_idx, row_idx + rowspan):
                for c in range(col_idx, col_idx + colspan):
                    grid[(r, c)] = (
                        cell_el, cell_tag, colspan, rowspan, row_idx, col_idx
                    )

            col_idx += colspan

    if not grid:
        return {}, 0, 0

    num_rows = max(r for r, _ in grid) + 1
    max_col = max(c for _, c in grid) + 1
    return grid, num_rows, max_col


def _extract_col_widths(table_el, resolver: CssResolver, max_col: int) -> list[float]:
    """Extract per-column widths (in pt) from <colgroup>/<col> elements.

    Returns an empty list if no explicit widths are found — the DOCX writer
    omits ``w:tblGrid`` in that case, letting Word auto-fit.
    """
    for child in table_el:
        if not isinstance(child.tag, str):
            continue
        if child.tag.lower() == "colgroup":
            widths: list[float] = []
            for col_el in child:
                if isinstance(col_el.tag, str) and col_el.tag.lower() == "col":
                    props = resolver.resolve(col_el)
                    w = css_value_to_pt(props.get("width", ""))
                    widths.append(w if w is not None else 0.0)
            if any(w > 0 for w in widths):
                return widths[:max_col]
    return []


# CSS border-style → OOXML w:val
_CSS_BORDER_STYLE: dict[str, str] = {
    "solid":   "single",
    "dashed":  "dashed",
    "dotted":  "dotted",
    "double":  "double",
    "groove":  "threeDEngrave",
    "ridge":   "threeDEmboss",
    "inset":   "inset",
    "outset":  "outset",
    "none":    "none",
    "hidden":  "none",
}

# CSS named border widths → pt
_CSS_BORDER_WIDTH: dict[str, float] = {
    "thin": 0.75, "medium": 2.25, "thick": 3.75,
}

# HTML <table border="N"> attribute — any positive value → default visible border
_HTML_BORDER_ATTR_DEFAULT = BorderDef(style="single", width_pt=0.5)


def _parse_border_shorthand(value: str) -> BorderDef | None:
    """Parse a CSS border shorthand ``'<width> <style> <color>'`` into a BorderDef.

    Returns ``BorderDef(style="none", width_pt=0)`` for ``border: none/0``,
    or ``None`` if the value is empty or unrecognised.
    """
    v = (value or "").strip()
    if not v:
        return None
    vl = v.lower()
    if vl in ("none", "0", "hidden"):
        return BorderDef(style="none", width_pt=0.0)

    style = "single"
    width_pt = 0.5
    color: str | None = None

    for part in v.split():
        pl = part.lower()
        if pl in _CSS_BORDER_STYLE:
            style = _CSS_BORDER_STYLE[pl]
        elif pl in _CSS_BORDER_WIDTH:
            width_pt = _CSS_BORDER_WIDTH[pl]
        else:
            pt = css_value_to_pt(part)
            if pt is not None:
                width_pt = max(0.0, pt)
            else:
                hex_color = _css_color_to_hex(part)
                if hex_color:
                    color = hex_color

    return BorderDef(style=style, width_pt=width_pt, color=color)


def _parse_table_borders(table_el, css: dict[str, str]) -> TableBorders | None:
    """Build a TableBorders from <table> CSS and the HTML ``border`` attribute.

    Returns ``None`` when no border CSS is present (writer will use its default).
    """
    # CSS ``border`` shorthand applies to all sides including inside rules
    if "border" in css:
        bd = _parse_border_shorthand(css["border"])
        if bd is not None:
            return TableBorders(
                top=bd, right=bd, bottom=bd, left=bd, inside_h=bd, inside_v=bd
            )

    # Per-side CSS
    top    = _parse_border_shorthand(css["border-top"])    if "border-top"    in css else None
    right  = _parse_border_shorthand(css["border-right"])  if "border-right"  in css else None
    bottom = _parse_border_shorthand(css["border-bottom"]) if "border-bottom" in css else None
    left   = _parse_border_shorthand(css["border-left"])   if "border-left"   in css else None
    if any(x is not None for x in (top, right, bottom, left)):
        return TableBorders(top=top, right=right, bottom=bottom, left=left)

    # HTML ``border`` attribute — legacy but common
    attr = (table_el.get("border") or "").strip()
    if attr:
        try:
            n = int(attr)
            if n == 0:
                bd_none = BorderDef(style="none", width_pt=0.0)
                return TableBorders(
                    top=bd_none, right=bd_none, bottom=bd_none, left=bd_none,
                    inside_h=bd_none, inside_v=bd_none,
                )
            # Positive value → visible single border, width proportional
            bd_vis = BorderDef(style="single", width_pt=min(n * 0.75, 6.0))
            return TableBorders(
                top=bd_vis, right=bd_vis, bottom=bd_vis, left=bd_vis,
                inside_h=bd_vis, inside_v=bd_vis,
            )
        except ValueError:
            pass

    return None  # no border CSS → writer uses its default


def _parse_cell_borders(css: dict[str, str]) -> TableBorders | None:
    """Build a TableBorders from <td>/<th> CSS for cell-level overrides."""
    if "border" in css:
        bd = _parse_border_shorthand(css["border"])
        if bd is not None:
            return TableBorders(top=bd, right=bd, bottom=bd, left=bd)

    top    = _parse_border_shorthand(css["border-top"])    if "border-top"    in css else None
    right  = _parse_border_shorthand(css["border-right"])  if "border-right"  in css else None
    bottom = _parse_border_shorthand(css["border-bottom"]) if "border-bottom" in css else None
    left   = _parse_border_shorthand(css["border-left"])   if "border-left"   in css else None

    if any(x is not None for x in (top, right, bottom, left)):
        return TableBorders(top=top, right=right, bottom=bottom, left=left)

    return None


def _bold_paragraph(para: Paragraph) -> Paragraph:
    """Return a copy of *para* with bold=True on every TextRun."""
    new_runs = tuple(
        dataclasses.replace(r, formatting=dataclasses.replace(r.formatting, bold=True))
        if isinstance(r, TextRun)
        else r
        for r in para.runs
    )
    return dataclasses.replace(para, runs=new_runs)
