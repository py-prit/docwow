# Round-tripping to DOCX

`docwow.to_docx()` converts a docwow HTML string back to a DOCX file.

!!! warning "docwow HTML only"
    `to_docx()` is designed to read HTML produced by `docwow.to_html()` or
    `docwow.render_document()`. It is **not** a general HTML-to-DOCX converter.
    Arbitrary HTML (from a website, rich-text editor, etc.) will produce
    unpredictable results or raise errors.

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

The round-trip preserves everything that docwow supports in v0.1:

- All paragraph formatting (alignment, indentation, spacing, page breaks)
- All run formatting (bold, italic, underline, strikethrough, font, size, color, highlight, super/subscript)
- Named styles (Heading1, Normal, custom styles)
- Tables (including col/row spans)
- Lists (bullet and numbered, nested)
- Inline images (original binary data restored from base64)
- Page geometry (width, height, margins)

## Using the low-level API

```python
import docwow

doc = docwow.parse_html(html)        # HTML → Document model
data = docwow.write_docx(doc)        # Document model → DOCX bytes

# Or write directly to a file
data = docwow.write_docx(doc, target="output.docx")
```
