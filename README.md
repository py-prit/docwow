# docwow

**Pure Python Word (DOCX) ↔ HTML conversion with guaranteed round-trip fidelity.**

docwow converts Word documents to a self-contained HTML representation and back again — without losing a single paragraph indent, table merge, list level, or inline image.

## Why docwow?

Existing libraries solve half the problem:

| Library | DOCX → HTML | HTML → DOCX | Round-trip |
|---|---|---|---|
| mammoth | good | — | — |
| python-docx | — | basic | — |
| **docwow** | **yes** | **yes** | **guaranteed** |

The key insight: docwow embeds every piece of Word metadata into `data-dw-*` HTML attributes alongside the visual CSS. The browser renders the CSS; when you convert back to DOCX, docwow reads the data attributes and reconstructs the original Word XML exactly.

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
| Programmatic API | Open, edit, and save documents in pure Python |

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

### 🗓 Roadmap

The project follows a phased plan. Contributors are welcome at any level.

#### Phase 2 — General HTML → DOCX (in progress)

Best-effort conversion of **arbitrary HTML** (not just docwow HTML) into DOCX. This makes docwow useful as a general-purpose HTML-to-Word exporter.

| Sub-feature | Status |
|---|---|
| Warnings + `is_foreign_html` flag | ✅ shipped |
| CSS cascade resolver + unit converter | ✅ shipped |
| Block elements (`h1`–`h6`, `p`, `div`, `blockquote`, `pre`, `hr`) | ✅ shipped |
| Inline elements (`b`/`i`/`u`/`s`/`code`/`mark`/`sub`/`sup`/`span`/`a` + CSS on runs) | ✅ shipped |
| Lists (`ul`/`ol`/`li`, nesting) | ✅ shipped |
| Tables (`table`/`tr`/`td`/`th`, colspan/rowspan) | pending |
| Images (`data:` URIs, `fetch_images` flag) | pending |

Entry point: `docwow/html_parser/generic/`.

#### Phase 2b — Floating images and text boxes

`wp:anchor` positioned images, text wrapping modes, and `w:txbx` inline text boxes. Currently anchored images are silently skipped.

#### Phase 3 — Tier 2 Word features

Individual features, all following the same 5-layer pattern (parser → renderer → html_parser → writer → API):

| Feature | OOXML element | Notes |
|---|---|---|
| Paragraph borders | `w:pBdr` | Box, shadow, bar borders |
| Columns | `w:cols` in `w:sectPr` | Multi-column layouts |
| Field codes | `w:instrText` | DATE, AUTHOR, TITLE fields |
| Bidi / RTL text | `w:bidi`, `w:rtl` | Right-to-left paragraphs |
| Hidden text | `w:vanish` | `display:none` in HTML |
| Per-section headers/footers | `w:headerReference` in inline `w:sectPr` | Different header after section break |
| Page number start | `w:pgNumType w:start` | Section-level page number reset |

#### How to contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, the 5-layer architecture pattern, testing requirements, and the PR process. One branch per feature, all layers in one PR.

## Documentation

Full documentation at [docwow.readthedocs.io](https://docwow.readthedocs.io).

## Requirements

- Python 3.10+
- lxml
- Pillow

## Built with Claude Code

This library was vibe coded using [Claude Code](https://claude.ai/code). Community suggestions, bug reports, and PRs are very welcome.

## License

MIT
