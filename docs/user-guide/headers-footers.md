# Headers, Footers & Page Numbers

docwow supports headers and footers with full DOCX round-trip fidelity. HTML rendering preserves all content for lossless conversion back to DOCX, but visual pagination in the browser is not yet implemented — see [known limitations](#known-limitations) below.

## Reading headers and footers from DOCX

When you open a DOCX file, headers and footers are available as properties on the document:

```python
import docwow

doc = docwow.open("document.docx")

# Default header (appears on all pages unless overridden)
if doc.header is not None:
    for para in doc.header.paragraphs:
        print(para.get_text())

# Default footer
if doc.footer is not None:
    for para in doc.footer.paragraphs:
        print(para.get_text())
```

### Slot types

Word supports three header/footer variants per document:

| Slot | Property | When it applies |
|---|---|---|
| Default | `doc.header` / `doc.footer` | All pages unless overridden |
| First page | `doc.header_first` / `doc.footer_first` | First page only, when `doc.title_pg` is `True` |
| Even pages | `doc.header_even` / `doc.footer_even` | Even-numbered pages |

```python
# Check if the document uses a different first-page header
if doc.title_pg:
    print("First page has a different header/footer")
    if doc.header_first is not None:
        print(doc.header_first.paragraphs[0].get_text())
```

### Page number fields

Paragraphs inside a header or footer may contain `MutablePageNumberField` runs:

```python
for para in doc.footer.paragraphs:
    for run in para.runs:
        if hasattr(run, "field_type"):   # it's a MutablePageNumberField
            print(run.field_type)        # "PAGE", "NUMPAGES", or "SECTIONPAGES"
```

## Adding headers and footers with the programmatic API

### Simple text header

```python
import docwow

doc = docwow.open("document.docx")

# Access (or create) the default header
hdr = doc.header           # lazy-creates a MutableHeaderFooter if absent
para = hdr.paragraphs.add_paragraph()
para.runs.add_text("My Company — Confidential")

doc.to_docx("output.docx")
```

### Footer with a page number field

```python
ftr = doc.footer
para = ftr.paragraphs.add_paragraph()
para.runs.add_text("Page ")
para.runs.add_page_number()           # inserts a PAGE field
para.runs.add_text(" of ")
para.runs.add_page_number("NUMPAGES") # inserts a NUMPAGES field

doc.to_docx("output.docx")
```

`add_page_number()` accepts one of three field types:

| Field type | Word inserts |
|---|---|
| `"PAGE"` (default) | Current page number |
| `"NUMPAGES"` | Total number of pages |
| `"SECTIONPAGES"` | Total pages in current section |

### Different first-page header

```python
doc.title_pg = True   # tell Word to use a different first-page header

first = doc.header_first
para = first.paragraphs.add_paragraph()
para.runs.add_text("Cover Page")      # shown on page 1 only

hdr = doc.header
para = hdr.paragraphs.add_paragraph()
para.runs.add_text("My Company")      # shown on pages 2+
```

### MutableHeaderFooter

`doc.header`, `doc.footer`, and the first/even variants all return a `MutableHeaderFooter`. It exposes a single collection:

| Property / Method | Description |
|---|---|
| `hf.paragraphs` | `ParagraphCollection` — add and iterate paragraphs |

### MutablePageNumberField

`add_page_number()` returns a `MutablePageNumberField`:

| Method | Description |
|---|---|
| `set_field_type(type)` | Change the field type — returns `self` for chaining |
| `field_type` | Property — the current field type string |

```python
field = para.runs.add_page_number()
field.set_field_type("NUMPAGES")
```

## Converting to HTML

### Header and footer elements

Headers and footers are rendered as HTML `<header>` and `<footer>` elements placed around the document body:

```html
<header class="dw-header dw-header-default" data-dw-header-type="default">
  <p class="dw-p">
    <span class="dw-r">My Company — Confidential</span>
  </p>
</header>

<div class="dw-document" ...>
  <!-- body content -->
</div>

<footer class="dw-footer dw-footer-default" data-dw-footer-type="default">
  <p class="dw-p">
    <span class="dw-r">Page </span>
    <span class="dw-field" data-dw-field="PAGE">1</span>
    <span class="dw-r"> of </span>
    <span class="dw-field" data-dw-field="NUMPAGES">1</span>
  </p>
</footer>
```

### Page number fields in HTML

Page number fields render as `<span class="dw-field" data-dw-field="PAGE">` with a static placeholder value of `1`. The placeholder is visible in the browser as gray italic text.

Paragraphs that consist entirely of page number fields and connector words (e.g. "Page N of M", "N / M") are given the `dw-page-only` CSS class and hidden from view — they are meaningless without real pagination. However, they remain in the DOM so the `data-dw-field` spans survive an HTML → DOCX conversion.

### Page breaks

Explicit page breaks are rendered as hidden `<div>` elements:

```html
<div class="dw-page-break" data-dw-page="2"></div>
```

The `data-dw-page` attribute records which page number follows the break. The div is always `display:none` in the browser.

### Page view (print / PDF)

Pass `page_view=True` to `render_document()` to add `@media print` CSS that sets the correct paper size and margins when the user prints or exports to PDF:

```python
html = docwow.render_document(doc, page_view=True)
```

This does not add visual page separators in the browser — it only affects the print stylesheet.

## Round-trip: HTML → DOCX

All header and footer content, including hidden page-number-only paragraphs, survives the HTML → DOCX round-trip:

```python
# DOCX → HTML → DOCX
html = docwow.to_html("original.docx")
docwow.to_docx(html, "restored.docx")
```

The `restored.docx` will contain:

- The same header text as the original
- The same footer with working page number fields (Word will render the correct numbers)
- Page breaks at the same positions

## Known limitations

See the [README](https://github.com/py-prit/docwow#%EF%B8%8F-headers-footers--page-numbers--known-limitations) for the full list. In brief:

- **Page numbers always show "1"** in the browser — no live page counting
- **No visual page separation** — the document looks like a single scroll
- **Header/footer appears once**, not repeated on every page
- **first-page and even-page slots** are preserved through DOCX round-trips but not applied per-page in HTML
- **Single document section** — mid-document section breaks with different headers are not supported
- **Page number start value** (`w:pgNumType w:start="N"`) is not parsed or written
