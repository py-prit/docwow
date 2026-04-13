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

## What's supported (v0.2)

- **Paragraphs** — alignment, indentation (left/right/first-line/hanging), spacing (before/after/line), page-break-before, keep-together, keep-with-next
- **Run formatting** — bold, italic, underline, strikethrough, font name, font size, color, highlight, superscript/subscript
- **Named styles** — Heading 1–9, Normal, and any custom styles defined in the document
- **Tables** — column widths, row heights, colspan, rowspan (vertical merge), cell borders
- **Lists** — bullet and numbered, nested up to any depth, multiple list instances per document
- **Inline images** — embedded as base64 data URIs in HTML, restored as binary data in DOCX
- **Programmatic API** — read and edit documents in Python via `DocumentWrapper`, `MutableParagraph`, `MutableRun`, and friends; build documents from scratch; save to DOCX or render to HTML

## Design principles

- **Pure Python** — no system dependencies beyond `lxml` and `Pillow`
- **Immutable models** — the internal `Document` model uses frozen dataclasses; safe to pass across threads or pipeline stages
- **Round-trip first** — every design decision is made with lossless DOCX→HTML→DOCX in mind
- **Not a general converter** — docwow reads its own HTML output back to DOCX; it does not attempt to convert arbitrary HTML
