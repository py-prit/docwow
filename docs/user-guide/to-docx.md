# Round-tripping to DOCX

`docwow.to_docx()` converts an HTML string to a DOCX file. It supports two modes:

- **Lossless round-trip** (default) — converts docwow-generated HTML back to DOCX with no data loss. All Word metadata is preserved via `data-dw-*` attributes.
- **Best-effort conversion** (`is_foreign_html=True`) — converts arbitrary HTML from any source (a CMS, rich text editor, web page, email) on a best-effort basis. See [Converting arbitrary HTML to DOCX](tutorial.md#18-converting-arbitrary-html-to-docx) in the tutorial.

## Basic usage

```python
import docwow

# Step 1: get the HTML (from to_html or your own storage)
html = docwow.to_html("original.docx")

# Step 2: convert back to DOCX
docx_bytes = docwow.to_docx(html)

# Step 3: save
with open("copy.docx", "wb") as f:
    f.write(docx_bytes)
```

## Writing directly to a file

Pass a `target` path to write the bytes to disk at the same time:

```python
docx_bytes = docwow.to_docx(html, target="output.docx")
# docx_bytes is also returned, in case you need it in memory too
```

## Accepting bytes input

```python
# HTML as UTF-8 bytes (e.g. from a database or HTTP POST body)
docx_bytes = docwow.to_docx(html.encode("utf-8"))
```

## Typical round-trip pattern

```python
import docwow

# User uploads a DOCX
original_bytes = request.files["doc"].read()

# Convert to HTML for browser display / editing
html = docwow.to_html(original_bytes)

# ... user edits the HTML in the browser, preserving data-dw-* attributes ...

# Convert the (possibly edited) HTML back to DOCX for download
edited_html = request.form["html"]
output_bytes = docwow.to_docx(edited_html)
```

## What's preserved

The round-trip preserves everything docwow supports:

- **Paragraph formatting** — alignment, indentation, spacing, keep-together, keep-with-next, page-break-before, paragraph borders, shading, tab stops
- **Run formatting** — bold, italic, underline, strikethrough, small caps, all caps, hidden text, font name/size, color, highlight, superscript/subscript, character styles
- **Named styles** — Heading 1–9, Normal, and any custom paragraph or character styles
- **Tables** — column and row spans, column/row widths, table styles, cell shading
- **Lists** — bullet and numbered, up to 9 nesting levels, all standard Word numbering formats
- **Inline images** — original binary data restored from base64 data URIs
- **Floating images** — position, text wrapping, anchor references, z-order
- **Hyperlinks** — external URLs and mailto links
- **Headers and footers** — text content, page number fields, all six slots (default/first/even × header/footer)
- **Page geometry** — page size and margins
- **Page breaks** — explicit page breaks and section breaks with independent geometry
- **Footnotes and endnotes** — note bodies and all reference markers in the document body
- **Bookmarks** — named anchor positions
- **Table of Contents** — title, entries, and anchor URLs
- **Comments** — author, date, initials, and multi-paragraph bodies; reference markers in the body
- **Track changes** — inserted and deleted runs with author, date, and accepted/rejected state
- **Field codes** — PAGE, NUMPAGES, SECTIONPAGES, DATE, TIME, AUTHOR, TITLE, FILENAME
- **Cross-references** — REF fields linking to named bookmarks

## Using the low-level API

```python
import docwow

doc = docwow.parse_html(html)        # HTML → Document model
data = docwow.write_docx(doc)        # Document model → DOCX bytes

# Or write directly to a file
data = docwow.write_docx(doc, target="output.docx")
```
