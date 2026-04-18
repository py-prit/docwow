# Changelog

All notable changes to docwow are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Paragraph borders (`w:pBdr`)** — `para.set_borders(ParagraphBorders(...))` adds box/rule/partial borders; `BorderDef` controls style, width, and color per side; full round-trip via `data-dw-borders`; CSS `border-*` in HTML
- **Hidden text (`w:vanish`)** — `run.set_vanish(True)` hides a run in Word; renders as `display:none` in HTML; full round-trip support across DOCX ↔ HTML ↔ DOCX
- `doc.find(text)` — search document body for paragraphs containing a string (case-sensitive)
- `doc.paragraphs.find(text)` / `para.find(text)` — search at collection and run level
- `doc.remove_footnote(note_id)` / `doc.remove_endnote(note_id)` — delete a note and all its reference markers
- `doc.remove_comment(comment_id)` — delete a comment and all its reference markers
- `MutableTableOfContents.remove_entry(entry)` / `.clear_entries()` — delete TOC entries

## [0.9.0] - 2026-04-18

### Added
- **Generic HTML → DOCX: Images** — `<img>` tags with `data:` URIs embedded directly; remote images fetched when `fetch_images=True`; automatic sizing preserves aspect ratio
- **Generic HTML → DOCX: Tables** — `<table>`, `<tr>`, `<td>`, `<th>`; `colspan`/`rowspan`; CSS border styles on cells; auto column width distribution
- **Generic HTML → DOCX: Lists** — `<ul>`/`<ol>`/`<li>` with up to 9 nesting levels; `decimal`, `lowerLetter`, `upperLetter`, `lowerRoman`, `upperRoman` formats; per-list numbering reset

## [0.8.0] - 2026-04-18

### Added
- **Generic HTML → DOCX: Inline elements** — `<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<mark>`, `<sub>`, `<sup>`, `<span>`, `<a>`; inline CSS mapped to run formatting (font family/size/color/weight/style)
- **Generic HTML → DOCX: Block elements** — `<h1>`–`<h6>`, `<p>`, `<div>`, `<blockquote>`, `<pre>`, `<hr>`; CSS text-align, margin, padding, font properties mapped to paragraph formatting
- **Generic HTML → DOCX: CSS resolver** — cascade resolver and unit converter; handles `px`, `pt`, `em`, `rem`, `%`; resolves inherited styles
- **`DocwowConversionWarning`** — structured warnings for unsupported constructs in foreign HTML; `docwow.suppress_warnings()` and `docwow.strict_warnings()` controls
- **`is_foreign_html` flag** — explicit opt-in for best-effort conversion of arbitrary HTML (not docwow-generated HTML)
- **CONTRIBUTING.md** — full contributor guide covering setup, 5-layer architecture, testing requirements, and PR process
- **IMPROVEMENTS.md** — technical debt backlog with effort estimates

## [0.7.0] - 2026-04-17

### Added
- **Paragraph and cell shading** — `w:shd` background colour on paragraphs and table cells; `set_shading()` API; `data-dw-shading` attribute; full round-trip
- **Character styles** — `w:rStyle` on runs; `set_char_style()` on `MutableRun`; `.dw-cstyle-*` CSS classes; full round-trip
- **Small caps and all caps** — `w:smallCaps` / `w:caps` run properties; `set_small_caps()` / `set_all_caps()` on `MutableRun`; full round-trip
- **Tab stops** — `w:tabs` in paragraph properties; `w:tab` run element; `set_tab_stops()` on `MutableParagraph`; full round-trip
- **Cross-references** — `REF` field via `w:fldChar`/`w:instrText`; renders as `<a class="dw-xref">`; `MutableCrossRef` API; `add_cross_ref()` on `RunCollection`; full round-trip
- **Multiple sections** — multiple `w:sectPr` with independent page size, margins, and break type; `MutableSectionBreak` API; `add_section_break()`; landscape orientation support; full round-trip
- **Track changes hover popup** — Accept/Reject buttons on `w:ins`/`w:del` annotations in HTML
- **Automated docstring coverage test** — `tests/api/test_api_docstrings.py` fails CI if any public API method is missing a docstring

### Changed
- Comprehensive docs audit — all API reference, tutorial, and HTML format docs brought up to date

## [0.6.0] - 2026-04-17

### Added
- **Bookmarks** — `w:bookmarkStart`/`w:bookmarkEnd`; renders as `<a id="…">` anchors; `MutableBookmark` API; full round-trip
- **Table of Contents** — `w:sdt` TOC blocks; renders as `<nav class="dw-toc">`; `MutableTableOfContents` API; full round-trip
- **Comments** — `word/comments.xml`; renders as superscript markers with CSS hover popups; `MutableComment` API; full round-trip
- **Track changes** — `w:ins`/`w:del`; renders as green underline / red strikethrough with author/date hover popup; `MutableTrackedChange` API; full round-trip

## [0.5.0] - 2026-04-13

### Added
- **Footnotes and endnotes** — parse, render to HTML with clickable ref links, HTML → DOCX round-trip, and `MutableFootnote` / `MutableEndnote` programmatic API

## [0.4.1] - 2026-04-13

### Added
- **Table editing API** — `MutableTable`, `MutableTableRow`, `MutableTableCell`; `add_table()` on `DocumentWrapper`; cell text, formatting, and merge access

## [0.4.0] - 2026-04-13

### Added
- **Headers and footers** — default, first-page, and even-page slots; `MutableHeaderFooter` API; full round-trip
- **Page number fields** — `PAGE`, `NUMPAGES`, `SECTIONPAGES` via `w:fldChar`; `MutablePageNumberField` API
- **Explicit page breaks** — `w:lastRenderedPageBreak` and `w:pageBreakBefore`; `data-dw-page` markers in HTML; full round-trip
- **Print / PDF export** — `render_document(doc, page_view=True)` injects `@media print` + `@page` CSS with correct paper size and margins

## [0.3.0] - 2026-04-13

### Added
- **Hyperlinks** — external URLs and `mailto:` links via `w:hyperlink`; renders as `<a href="…">`; full round-trip

## [0.2.0] - 2026-04-13

### Added
- **Programmatic API** — `DocumentWrapper`, `ParagraphCollection`, `MutableParagraph`, `MutableRun`, `RunCollection`; open, edit, and save documents in pure Python without touching XML
- **Read the Docs** — documentation live at [docwow.readthedocs.io](https://docwow.readthedocs.io)

## [0.1.0] - 2026-04-11

### Added
- Initial release
- **DOCX → HTML** conversion with `data-dw-*` attribute metadata for lossless round-trip
- **HTML → DOCX** round-trip (docwow-generated HTML only)
- Paragraphs — text, alignment, indentation, spacing, keep-together/with-next, page-break-before
- Run formatting — bold, italic, underline, strikethrough, font name/size, colour, highlight, superscript/subscript
- Named paragraph styles — Heading 1–9, custom styles, full style ID round-trip
- Tables — column spans, row spans (`vMerge`), column/row widths, table-level styles
- Lists — bullet and numbered, up to 9 nesting levels, all standard Word numbering formats
- Inline images — PNG, JPEG, GIF, BMP, TIFF, WebP, SVG, EMF, WMF
- Page geometry — page size and margins

[Unreleased]: https://github.com/py-prit/docwow/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/py-prit/docwow/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/py-prit/docwow/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/py-prit/docwow/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/py-prit/docwow/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/py-prit/docwow/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/py-prit/docwow/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/py-prit/docwow/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/py-prit/docwow/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/py-prit/docwow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/py-prit/docwow/releases/tag/v0.1.0
