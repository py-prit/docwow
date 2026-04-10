# Converting to HTML

`docwow.to_html()` converts a DOCX file to a self-contained HTML string.

## Basic usage

```python
import docwow

html = docwow.to_html("report.docx")
```

The returned string is a complete HTML document — `<!DOCTYPE html>`, `<head>` with embedded CSS, and `<body>` with the document content.

## Input formats

```python
# From a file path (str or Path)
html = docwow.to_html("report.docx")
html = docwow.to_html(Path("report.docx"))

# From raw bytes (e.g. read from a database or HTTP response)
with open("report.docx", "rb") as f:
    data = f.read()
html = docwow.to_html(data)
```

## Saving to disk

```python
html = docwow.to_html("report.docx")
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)
```

## Serving over HTTP

```python
# Flask example
from flask import Response
import docwow

@app.route("/view/<filename>")
def view_doc(filename):
    html = docwow.to_html(f"uploads/{filename}")
    return Response(html, content_type="text/html; charset=utf-8")
```

## Using the low-level API

`to_html()` is a convenience wrapper around two lower-level functions:

```python
import docwow

doc = docwow.parse_docx("report.docx")   # DOCX → Document model
html = docwow.render_document(doc)        # Document model → HTML
```

Use the low-level API when you need to inspect or modify the `Document` model between parsing and rendering.

## What's in the output

- A `<style>` block with base CSS and per-style rules
- A `<div class="dw-document">` containing paragraphs, tables, and lists
- All images embedded as base64 data URIs
- All Word metadata preserved in `data-dw-*` attributes

See [HTML Format Overview](../html-format/overview.md) for the full structure.
