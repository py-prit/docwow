# Hyperlinks

docwow supports external hyperlinks (URLs and mailto links) with full round-trip fidelity through both HTML and DOCX.

## Reading hyperlinks from DOCX

When you open a DOCX file containing hyperlinks, each link becomes a `Hyperlink` run on its paragraph:

```python
import docwow

doc = docwow.open("document.docx")

for para in doc.paragraphs:
    for run in para.runs:
        if hasattr(run, "url"):   # it's a MutableHyperlink
            print(run.url, run.get_text())
```

## Adding hyperlinks with the programmatic API

Use `runs.add_hyperlink()` to add a hyperlink to any paragraph:

```python
import docwow

doc = docwow.open("document.docx")
para = doc.paragraphs.add_paragraph()

# Add plain text before the link
para.runs.add_text("Visit the ")

# Add a hyperlink
para.runs.add_hyperlink(text="docwow documentation", url="https://docwow.readthedocs.io")

# Add plain text after
para.runs.add_text(" for more details.")

doc.to_docx("output.docx")
```

### MutableHyperlink

`add_hyperlink()` returns a `MutableHyperlink` which supports chained setters:

```python
link = para.runs.add_hyperlink("Click here", "https://example.com")
link.set_text("Read the docs").set_url("https://docwow.readthedocs.io")
```

| Method | Description |
|---|---|
| `set_text(text)` | Change the visible link text |
| `set_url(url)` | Change the URL |
| `get_text()` | Return the current link text |
| `url` | Property — the current URL |

### Supported URL schemes

| Scheme | Example |
|---|---|
| `https://` | `https://example.com` |
| `http://` | `http://example.com` |
| `mailto:` | `mailto:hello@example.com` |
| `ftp://` | `ftp://example.com` |

## Converting to HTML

Hyperlinks are rendered as standard `<a>` elements:

```python
html = docwow.to_html("document.docx")
# <a href="https://example.com" class="dw-hyperlink"
#    data-dw-href="https://example.com">
#   <span class="dw-r">Click here</span>
# </a>
```

The URL is written to both `href` (for browsers) and `data-dw-href` (for round-trip reconstruction). Special characters in URLs are HTML-escaped automatically.

## Round-tripping HTML back to DOCX

Any HTML produced by docwow round-trips back to DOCX preserving the hyperlink URL and text:

```python
html = docwow.to_html("document.docx")
docwow.to_docx(html, "output.docx")
```

The resulting DOCX contains a proper `word/_rels/document.xml.rels` entry:

```xml
<Relationship Id="rId5"
  Type=".../hyperlink"
  Target="https://example.com"
  TargetMode="External"/>
```

## Limitations

- **In-document anchor links** (e.g. links that jump to a heading within the same file) are parsed and stored as `Hyperlink(url="#bookmark-name")`, but the bookmark *targets* are not yet supported. The link text is preserved through round-trips; clickable navigation requires bookmark support (planned).
- The link text is stored as a single string in the programmatic API. Multi-run hyperlinks (e.g. bold mid-link) are flattened to plain text on open.
