# docwow

[![PyPI version](https://img.shields.io/pypi/v/docwow)](https://pypi.org/project/docwow/)
[![CI](https://github.com/py-prit/docwow/actions/workflows/ci.yml/badge.svg)](https://github.com/py-prit/docwow/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-%E2%89%A590%25-brightgreen)](https://github.com/py-prit/docwow/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/docwow)](https://pypi.org/project/docwow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pure Python Word (DOCX) ↔ HTML conversion with guaranteed round-trip fidelity.**

docwow converts Word documents to a self-contained HTML representation and back again — without losing a single paragraph indent, table merge, list level, footnote, comment, or inline image. It also converts arbitrary HTML from any source into DOCX on a best-effort basis.

## Why docwow?

Working with Word documents in Python usually means reaching for multiple tools — one for rendering to HTML, another for programmatic editing, another for writing DOCX output. docwow covers all of it in a single library with a unified model:

- **DOCX → HTML** — render any Word document to self-contained HTML for browser display, web apps, or archival storage
- **HTML → DOCX (lossless round-trip)** — convert docwow HTML back to DOCX with guaranteed fidelity; not a single paragraph indent, table merge, list level, footnote, comment, or inline image is lost
- **Arbitrary HTML → DOCX** — convert HTML from any source — a CMS, rich text editor, web page, or email — to a properly formatted Word document
- **Programmatic API** — open, read, edit, and build Word documents in pure Python without touching XML; every feature accessible via a clean, chainable API

The key insight behind the round-trip: rather than inferring Word semantics from CSS (which is lossy), docwow embeds the original Word metadata directly into `data-dw-*` HTML attributes. The browser renders the CSS; when you convert back to DOCX, docwow reads the data attributes and reconstructs the original Word XML exactly.

**Battle-tested:** stress-tested against 176 real-world DOCX files from the Apache POI corpus — 159/176 round-trip with zero data loss. The remaining 17 are invalid, encrypted, or password-protected files. 2,552 tests across all five pipeline layers with ≥ 90% coverage.

## Install

```bash
pip install docwow
```

## Quick Start

```python
import docwow

# DOCX → HTML
html = docwow.to_html("document.docx")

# docwow HTML → DOCX (lossless round-trip)
docwow.to_docx(html, "output.docx")

# Arbitrary HTML → DOCX (best-effort, any source)
docwow.to_docx("<h1>Title</h1><p>Body text.</p>", "output.docx", is_foreign_html=True)

# Or use the Document object for programmatic editing
doc = docwow.open("document.docx")
para = doc.paragraphs.add_paragraph()
para.runs.add_text("Hello world", bold=True)
doc.to_docx("output.docx")
```

Control conversion warnings:

```python
import docwow

docwow.suppress_warnings()   # silence all DocwowConversionWarnings
docwow.strict_warnings()     # raise on any unsupported construct (useful in CI)
```

## Feature Support

### ✅ Supported

| Feature | Notes |
|---|---|
| Paragraphs | Text, alignment, indentation, spacing, keep-together/with-next, page-break-before |
| Run formatting | Bold, italic, underline, strikethrough, small caps, all caps, font name/size, colour, highlight, superscript/subscript |
| Tab stops | Custom paragraph tab stops (`w:tabs`), tab character runs (`w:tab`), `set_tab_stops()` API, full round-trip |
| Cross-references | REF fields linking to named bookmarks; renders as `<a class="dw-xref">`, `MutableCrossRef` API, full round-trip |
| Multiple sections | Multiple `w:sectPr` with independent page size, margins, and break type; `MutableSectionBreak` API, full round-trip |
| Inline images | PNG, JPEG, GIF, BMP, TIFF, WebP, SVG, EMF, WMF |
| Tables | Column spans, row spans (vMerge), column/row widths, table-level styles; fully editable via programmatic API |
| Lists | Bullet and numbered, up to 9 nesting levels, decimal/lowerLetter/upperLetter/lowerRoman/upperRoman formats |
| Hyperlinks | External URLs, mailto links |
| Paragraph styles | Style ID round-trip, Heading 1–9 and custom styles |
| Page geometry | Page size, margins |
| Headers & footers | Text content, page number fields, default/first/even slots — see limitations below |
| Page breaks | Explicit page breaks parsed, written, and round-tripped |
| Footnotes & endnotes | Parse, render to HTML, HTML → DOCX round-trip, and programmatic API |
| Bookmarks | Parse `w:bookmarkStart`, render as `<a id="…">` anchors, full round-trip, `MutableBookmark` API |
| Table of Contents | Parse `w:sdt` TOC blocks, render as `<nav class="dw-toc">`, full round-trip, `MutableTableOfContents` API |
| Comments | Parse `word/comments.xml`, render as superscript markers with CSS hover popups in HTML, full round-trip, `MutableComment` API |
| Track changes | Parse `w:ins`/`w:del`, render as green underline / red strikethrough with hover popup (author, date, Accept/Reject buttons) in HTML, full round-trip, `MutableTrackedChange` API |
| Paragraph borders | Box, rule, and partial borders (`w:pBdr`); `set_borders()` API, full round-trip via `data-dw-borders` |
| Field codes | `DATE`, `TIME`, `AUTHOR`, `TITLE`, `FILENAME` fields alongside `PAGE`/`NUMPAGES`/`SECTIONPAGES`; static placeholders in HTML, full round-trip |
| Hidden text | `w:vanish` → `display:none` in HTML; `set_vanish()` API, full round-trip |
| Floating images | Positioned (`wp:anchor`) images with `square`, `tight`, `topAndBottom`, `through`, and `none` text wrapping; `MutableFloatingImageRun` API, full round-trip |
| Programmatic API | Open, edit, and save documents in pure Python; `doc.find()`, `doc.remove_footnote()`, `doc.remove_comment()`, and more |

### ⚠️ Headers, Footers & Page Numbers — Known Limitations

Headers and footers are supported for DOCX round-trips and basic HTML rendering, but several aspects are incomplete. These are intentional deferments, not bugs.

#### What works

- **DOCX ↔ DOCX round-trip** — all six slots (default/first/even × header/footer), page number fields (`PAGE`, `NUMPAGES`, `SECTIONPAGES`), and the `title_pg` flag survive a full write → parse cycle with no data loss.
- **HTML rendering** — headers and footers with real text content are rendered as `<header>` / `<footer>` elements visible in the browser.
- **DOCX → HTML → DOCX round-trip** — page-number-only paragraphs (e.g. "Page N of M") are kept as hidden elements in the HTML (`display:none`) so the fields survive the HTML → DOCX leg. The output DOCX will have a working page-number footer in Word.
- **Print / PDF export** — `render_document(doc, page_view=True)` injects `@media print` + `@page` CSS with the correct paper size and margins, so Cmd+P / browser PDF export paginates correctly.

#### What does not work (and why)

**1. Page numbers always show "1" in the browser**

Page number fields render as a static placeholder `1`. Correct values require knowing which page each element lands on, which requires measuring rendered element heights — something only the browser layout engine can do after paint. Without a layout measurement API or a third-party pagination library, this cannot be solved in a pre-render Python step. *Possible approach for contributors:* use a small post-render JS snippet that walks `data-dw-field` spans and updates them after the browser has laid out the page, combined with `data-dw-page` markers on page-break divs.

**2. No visual page separation in the browser**

Explicit page breaks are preserved as hidden `<div class="dw-page-break" data-dw-page="N">` elements but produce no visible gap. Making pages visually discrete requires either CSS `@page` (print-only, not interactive) or JS that measures element heights to insert separators — again a layout-engine problem. *Possible approach:* a small inline JS block that reads the `dw-page-break` markers and inserts visual dividers, sizing each page section to the document's `data-dw-page-height`.

**3. Header and footer appear once, not on every page**

In Word, headers and footers repeat at the top/bottom of every page. In HTML there is a single `<header>` and `<footer>` element. Making them repeat requires knowing page boundaries (see point 2). *Possible approach:* same JS pagination pass — once page sections are created, clone the header/footer HTML into each section.

**4. first-page and even-page slots not applied in HTML**

The `title_pg` flag and even-page slots are preserved through DOCX round-trips but the HTML renderer emits all slots regardless. No CSS or JS selects the right slot per page. *Possible approach:* after the JS pagination pass, inspect the `data-dw-title-pg` attribute on the document div and apply `header-first` vs `header-default` to the appropriate page sections.

**5. Page number start value not supported**

DOCX allows `<w:pgNumType w:start="N"/>` to start numbering from a value other than 1. Not currently parsed or written. *Possible approach:* add `page_num_start: int = 1` to the `Document` model and read/write it from `w:sectPr`.

### 🗓 Planned

The items below represent the committed future direction of docwow, in rough priority order.

#### Round-trip fidelity gaps (identified v1.0.2 audit)

These are properties that exist in real DOCX files but are currently dropped on the DOCX → HTML → DOCX round-trip:

| Area | Missing properties |
|---|---|
| Run formatting | Complex-script bold/italic/size (`bCs`/`iCs`/`szCs`), font kerning, double strikethrough, run border, character spacing, run shading, language (`w:lang`), no-proof flag |
| Paragraph formatting | Paragraph-mark formatting (`w:pPr/w:rPr`), contextual spacing, style-attached numbering (`w:numPr` in style definitions) |
| Tables | Table width, cell vertical alignment, cell margins, individual cell borders, cell spacing, table conditional formatting |
| Section properties | Multi-column layout (`w:cols`), document grid (`w:docGrid`) |
| Field codes | TC fields (TOC entry markers), TOC regeneration field, PAGEREF cross-reference fields |
| Document parts | Theme colours/fonts (`theme1.xml`), document metadata (`core.xml`/`app.xml`), full settings passthrough |

#### DOCX → PDF (pure Python, no LibreOffice)

Direct `Document` model → PDF output pipeline — no HTML intermediate, no external binaries, no LibreOffice. Pure Python using ReportLab for PDF primitives and fonttools for font metrics. Planned in two phases:

- **Phase 1** — Paragraphs, run formatting, headings, page breaks, inline images, basic tables, lists
- **Phase 2** — Headers/footers repeated per page, footnotes, column layout, TOC with live page numbers

#### Other

- Visual page separation and correct page numbers in browser HTML (requires JS layout pass)
- Header/footer repeating per page in browser HTML

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, the architecture pattern, and the PR process.

## Documentation

Full documentation at [docwow.readthedocs.io](https://docwow.readthedocs.io).

## Requirements

- Python 3.10+
- lxml
- Pillow

## Contributing

Bug reports, feature requests, and PRs are very welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## License

MIT
