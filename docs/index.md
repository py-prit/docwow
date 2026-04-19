# docwow

**Pure Python Word (DOCX) ↔ HTML conversion with guaranteed round-trip fidelity.**

docwow converts Word documents to a self-contained HTML representation and back again — without losing a single paragraph indent, table merge, list level, or inline image.

## Why docwow?

Working with Word documents in Python usually means reaching for multiple tools — one for rendering to HTML, another for programmatic editing, another for writing DOCX output. docwow covers all of it in a single library with a unified model:

- **DOCX → HTML** — render any Word document to self-contained HTML for browser display, web apps, or archival storage
- **HTML → DOCX (lossless round-trip)** — convert docwow HTML back to DOCX with guaranteed fidelity; not a single paragraph indent, table merge, list level, footnote, comment, or inline image is lost
- **Arbitrary HTML → DOCX** — convert HTML from any source — a CMS, rich text editor, web page, or email — to a properly formatted Word document
- **Programmatic API** — open, read, edit, and build Word documents in pure Python without touching XML; every feature accessible via a clean, chainable API

The key insight behind the round-trip: rather than inferring Word semantics from CSS (which is lossy), docwow embeds the original Word metadata directly into `data-dw-*` HTML attributes. The browser renders the CSS; when you convert back to DOCX, docwow reads the data attributes and reconstructs the original Word XML exactly.

## Install

```bash
pip install docwow
```

## Quick Start

```python
import docwow

# DOCX → HTML
html = docwow.to_html("report.docx")

# HTML → DOCX (round-trip)
docx_bytes = docwow.to_docx(html)
with open("report-copy.docx", "wb") as f:
    f.write(docx_bytes)

# Open and edit a document programmatically
doc = docwow.open("report.docx")
doc.paragraphs[0].set_text("New title").set_style("Heading1")
doc.paragraphs.add_paragraph("Added paragraph.")
doc.save("updated.docx")
```

## What's supported

- **Paragraphs** — alignment, indentation (left/right/first-line/hanging), spacing (before/after/line), page-break-before, keep-together, keep-with-next
- **Run formatting** — bold, italic, underline, strikethrough, small caps, all caps, font name, font size, color, highlight, superscript/subscript, hidden text (`w:vanish`)
- **Tab stops** — custom paragraph tab stops (`w:tabs`), tab character runs (`w:tab`), full round-trip via `data-dw-tab-stops`
- **Cross-references** — REF fields linking to named bookmarks; renders as `<a class="dw-xref">`, full round-trip, `MutableCrossRef` API
- **Multiple sections** — multiple `w:sectPr` with independent page size, margins, and break type; `MutableSectionBreak` API, full round-trip via `data-dw-section-break`
- **Named styles** — Heading 1–9, Normal, and any custom styles defined in the document
- **Tables** — column widths, row heights, colspan, rowspan (vertical merge), cell borders
- **Lists** — bullet and numbered, nested up to any depth, multiple list instances per document
- **Inline images** — embedded as base64 data URIs in HTML, restored as binary data in DOCX
- **Hyperlinks** — external URLs and mailto links, with full round-trip fidelity
- **Headers & footers** — text content and page number fields across default, first-page, and even-page slots
- **Page breaks** — explicit page breaks parsed, written, and round-tripped
- **Footnotes & endnotes** — parse, render to HTML with anchor links, HTML→DOCX round-trip, and programmatic API
- **Bookmarks** — parse `w:bookmarkStart` elements, render as `<a id="…">` HTML anchors, full round-trip, and `MutableBookmark` API
- **Table of Contents** — parse `w:sdt` TOC blocks, render as `<nav class="dw-toc">` with level-indented links, full round-trip, and `MutableTableOfContents` API
- **Comments** — parse `word/comments.xml`, render as superscript markers with CSS hover popups in HTML, full round-trip, and `MutableComment` API
- **Track changes** — parse `w:ins`/`w:del`, render as green underline / red strikethrough with hover popup (author, date, Accept/Reject buttons) in HTML, accepted/rejected state preserved on HTML→DOCX round-trip, and `MutableTrackedChange` API
- **Paragraph borders** — box, rule, and partial borders (`w:pBdr`); `set_borders()` API; full round-trip via `data-dw-borders`; CSS `border-*` in HTML
- **Field codes** — `DATE`, `TIME`, `AUTHOR`, `TITLE`, `FILENAME` alongside `PAGE`/`NUMPAGES`/`SECTIONPAGES`; static placeholders in HTML; full round-trip
- **Floating images** — positioned (`wp:anchor`) images with `square`, `tight`, `topAndBottom`, `through`, and `none` text wrapping; horizontal/vertical offsets and anchor frames; `behind_doc` z-order; `MutableFloatingImageRun` API; full round-trip via `<figure class="dw-float-img">` with `data-dw-float-*` attributes
- **Programmatic API** — read and edit documents in Python via `DocumentWrapper`, `MutableParagraph`, `MutableRun`, `MutableBookmark`, `MutableTable`, `MutableTableOfContents`, `MutableComment`, `MutableFloatingImageRun`, and friends; build documents from scratch including tables, footnotes, bookmarks, TOC, comments, and lists; `doc.find()`, `doc.remove_footnote()`, `doc.remove_comment()`, and more; save to DOCX or render to HTML

## Design principles

- **Pure Python** — no system dependencies beyond `lxml` and `Pillow`
- **Immutable models** — the internal `Document` model uses frozen dataclasses; safe to pass across threads or pipeline stages
- **Round-trip first** — every design decision is made with lossless DOCX→HTML→DOCX in mind
- **Two conversion paths** — lossless round-trip for docwow HTML, and best-effort conversion for arbitrary HTML from any source (`is_foreign_html=True`)
