# HTML Format Overview

docwow produces a single, self-contained HTML file from a DOCX document. This page describes the overall structure of that output.

## Document structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Document</title>
  <style>
    /* docwow base styles */
    /* per-style rules (.dw-style-Heading1, etc.) */
    /* document geometry (.dw-document max-width, padding) */
  </style>
</head>
<body>
  <div class="dw-document" data-dw-page-width="595.28" ...>
    <!-- paragraphs, tables, lists -->
  </div>
</body>
</html>
```

## Two-layer design

Each element carries two independent layers of information:

**Layer 1 — Visual (CSS)**

CSS classes and inline styles control how the document looks in a browser. The base stylesheet (`.dw-document`, `.dw-p`, `.dw-r`, `.dw-table`, etc.) provides structural defaults. Named Word styles are emitted as additional CSS classes (`.dw-style-Heading1`, `.dw-style-Normal`, etc.).

**Layer 2 — Metadata (`data-dw-*` attributes)**

Every piece of Word-specific information that has no CSS equivalent is stored in `data-dw-*` HTML attributes. Examples: exact point dimensions, list numbering IDs, vertical cell merges, image content types. These attributes are invisible in the browser but are read back by the HTML parser when converting to DOCX.

## CSS classes reference

| Class | Element | Purpose |
|---|---|---|
| `.dw-document` | `<div>` | Page container (max-width, padding from margins) |
| `.dw-p` | `<p>` | Paragraph |
| `.dw-r` | `<span>` | Run (inline text with formatting) |
| `.dw-table` | `<table>` | Table |
| `.dw-tr` | `<tr>` | Table row |
| `.dw-td` | `<td>` | Table cell |
| `.dw-list` | `<ul>` / `<ol>` | List container |
| `.dw-li` | `<li>` | List item |
| `.dw-img` | `<img>` | Inline image |
| `.dw-bookmark` | `<a>` | Zero-width bookmark anchor |
| `.dw-footnote-ref` | `<a>` | Inline footnote reference marker |
| `.dw-endnote-ref` | `<a>` | Inline endnote reference marker |
| `.dw-footnotes` | `<section>` | Footnote bodies section |
| `.dw-endnotes` | `<section>` | Endnote bodies section |
| `.dw-toc` | `<nav>` | Table of Contents block |
| `.dw-toc-link` | `<a>` | Clickable TOC entry link |
| `.dw-comment-ref` | `<a>` | Inline comment reference marker (orange superscript) |
| `.dw-comments` | `<section>` | Hidden comment metadata section (round-trip only) |
| `ins.dw-ins` | `<ins>` | Tracked insertion (green underline) |
| `del.dw-del` | `<del>` | Tracked deletion (red strikethrough) |
| `.dw-page-break` | `<div>` | Explicit page break (hidden, round-trip only) |
| `.dw-page-only` | `<p>` | Page-number-only paragraph (hidden, round-trip only) |
| `.dw-field` | `<span>` | Page number field placeholder |
| `.dw-style-{StyleId}` | `<p>` | Named Word style applied to a paragraph |

## Self-contained

The HTML output is almost entirely self-contained:

- All styles are inlined in a `<style>` block — no external CSS
- All images are embedded as base64 data URIs — no external files
- A small inline `<script>` block is injected at the end of `<body>` to power the track-changes Accept/Reject buttons (`dwTcAccept` / `dwTcReject`). It has no external dependencies.

This means a docwow HTML file can be saved to disk, emailed, or stored in a database and opened anywhere without needing the original DOCX.
