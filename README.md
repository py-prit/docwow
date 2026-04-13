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

# HTML → DOCX (round-trip)
docwow.to_docx(html, "output.docx")

# Or use the Document object for programmatic editing
doc = docwow.open("document.docx")
para = doc.paragraphs.add_paragraph()
para.runs.add_text("Hello world", bold=True)
doc.to_docx("output.docx")
```

## Feature Support

### ✅ Supported

| Feature | Notes |
|---|---|
| Paragraphs | Text, alignment, indentation, spacing, keep-together/with-next, page-break-before |
| Run formatting | Bold, italic, underline, strikethrough, font name/size, colour, highlight, superscript/subscript |
| Inline images | PNG, JPEG, GIF, BMP, TIFF, WebP, SVG, EMF, WMF |
| Tables | Column spans, row spans (vMerge), column/row widths, table-level styles |
| Lists | Bullet and numbered, up to 9 nesting levels, decimal/lowerLetter/upperLetter/lowerRoman/upperRoman formats |
| Hyperlinks | External URLs, mailto links |
| Paragraph styles | Style ID round-trip, Heading 1–9 and custom styles |
| Page geometry | Page size, margins |
| Programmatic API | Open, edit, and save documents in pure Python |

### 🚧 In Progress

Nothing currently — check back soon.

### 🗓 Planned

| Feature | Notes |
|---|---|
| Headers & footers | Including page numbers |
| Table of contents | Requires bookmark support |
| Bookmarks | In-document anchor links and TOC targets |
| Comments | Annotations / review marks |
| Track changes | Accept/reject revision marks |
| Footnotes & endnotes | |
| General HTML → DOCX | Best-effort conversion of arbitrary HTML (not just docwow HTML) |

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
