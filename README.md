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

# Or use the Document object
doc = docwow.open("document.docx")
html = doc.to_html()
doc.to_docx("output.docx")
```

## Documentation

Full documentation at [docwow.dev](https://docwow.dev).

## Requirements

- Python 3.10+
- lxml
- Pillow

## License

MIT
