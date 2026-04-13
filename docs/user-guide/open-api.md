# Programmatic API

`docwow.open()` returns a `DocumentWrapper` — a mutable object that lets you read, edit, and build Word documents in Python without touching XML.

## Opening a document

```python
import docwow

# From a file path
doc = docwow.open("report.docx")

# From DOCX bytes
with open("report.docx", "rb") as f:
    doc = docwow.open(f.read())

# From a docwow HTML string
html = docwow.to_html("report.docx")
doc = docwow.open(html)
```

`open()` auto-detects the input: DOCX files (by path extension or ZIP magic bytes) go through the DOCX parser; anything else is treated as a docwow HTML string.

## Saving output

```python
# Write to a file
doc.save("output.docx")

# Get bytes (useful for HTTP responses)
data = doc.to_bytes()

# Render back to HTML
html = doc.to_html()
```

## Reading document content

### Iterating body elements

```python
from docwow.api import MutableParagraph, TableView

for item in doc.paragraphs:
    if isinstance(item, TableView):
        print(f"Table with {len(item)} rows")
    else:
        print(item.get_text())
```

### Reading paragraph text and formatting

```python
para = doc.paragraphs[0]
print(para.get_text())    # full text of all runs concatenated
print(para.style_id)      # e.g. "Heading1"
print(para.alignment)     # "left", "center", "right", "justify", or None
```

### Reading runs

```python
from docwow.api import MutableRun, MutableImageRun

for run in para.runs:
    if isinstance(run, MutableRun):
        print(run.get_text(), run.bold, run.italic, run.font_size)
    elif isinstance(run, MutableImageRun):
        print(f"Image: {run.width_pt}x{run.height_pt}pt")
```

### Reading tables (read-only in v0.2)

```python
from docwow.api import TableView

for item in doc.paragraphs:
    if isinstance(item, TableView):
        for row in item:
            for cell in row:
                print(cell.get_text())
```

## Editing existing content

### Editing paragraph text and formatting

All setters return `self`, so they are chainable:

```python
para = doc.paragraphs[0]
para.set_text("Updated title").set_alignment("center").set_style("Heading1")
```

### Editing individual runs

```python
run = para.runs[0]
run.set_text("New text").set_bold(True).set_color("FF0000")
```

### Run formatting options

```python
run.set_bold(True)
run.set_italic(True)
run.set_underline(True)
run.set_strike(True)
run.set_font_name("Arial")
run.set_font_size(14.0)               # in points
run.set_color("FF0000")               # hex RGB, no '#'
run.set_highlight("yellow")
run.set_vertical_align("superscript") # or "subscript"
```

### Paragraph-level formatting (applies to all runs)

```python
para.set_bold(True)
para.set_italic(True)
para.set_underline(True)
para.set_font_name("Arial")
para.set_font_size(12.0)
para.set_color("333333")
para.set_alignment("justify")
para.set_indent(left_pt=36.0, right_pt=0.0, first_line_pt=18.0)
para.set_spacing(before_pt=6.0, after_pt=6.0, line_pt=14.0)
para.set_keep_together(True)
para.set_keep_with_next(True)
para.set_page_break_before(True)
```

## Building a document from scratch

```python
from docwow.api import DocumentWrapper

doc = DocumentWrapper()

# Add a heading
doc.paragraphs.add_paragraph("Quarterly Report", style_id="Heading1")

# Add body text with mixed formatting
para = doc.paragraphs.add_paragraph()
para.runs.add_text("Revenue grew by ")
para.runs.add_text("42%", bold=True, color="2E7D32")
para.runs.add_text(" this quarter.")

# Add a bulleted list
num_id = doc.add_numbering_definition(num_fmt="bullet")
doc.paragraphs.add_list_item("First point", num_id=num_id, level=0)
doc.paragraphs.add_list_item("Sub-point", num_id=num_id, level=1)
doc.paragraphs.add_list_item("Second point", num_id=num_id, level=0)

# Add a numbered list
num_id2 = doc.add_numbering_definition(num_fmt="decimal")
doc.paragraphs.add_list_item("Step one", num_id=num_id2)
doc.paragraphs.add_list_item("Step two", num_id=num_id2)

# Add an image
with open("logo.png", "rb") as f:
    img_data = f.read()
doc.paragraphs.add_image(
    img_data, content_type="image/png", width_pt=200.0, height_pt=100.0
)

doc.save("report.docx")
```

## Working with lists

### `add_numbering_definition(num_fmt)`

Registers a new list style and returns its `num_id`. Pass that `num_id` when adding list items.

```python
num_id = doc.add_numbering_definition(num_fmt="bullet")
# num_fmt options: "bullet", "decimal", "lowerLetter", "upperLetter",
#                  "lowerRoman", "upperRoman"
```

### Adding and adjusting list items

```python
item = doc.paragraphs.add_list_item("Buy milk", num_id=num_id, level=0)
item.set_level(1)           # change nesting depth
item.set_num_id(other_id)   # switch to a different list
```

## Page geometry

```python
# Read
print(doc.page_width_pt, doc.page_height_pt)
print(doc.margin_top_pt, doc.margin_bottom_pt)
print(doc.margin_left_pt, doc.margin_right_pt)

# Set (A4 with 1-inch margins)
doc.set_page_size(595.28, 841.89)
doc.set_margins(top_pt=72.0, bottom_pt=72.0, left_pt=72.0, right_pt=72.0)
```

## ParagraphCollection reference

`doc.paragraphs` is a `ParagraphCollection` — an ordered, mutable list of body elements.

| Method | Description |
|---|---|
| `add_paragraph(text, style_id)` | Create and append a paragraph, return it |
| `add_list_item(text, level, num_id)` | Create and append a list item, return it |
| `add_image(data, content_type, width_pt, height_pt, alt_text)` | Create and append an image paragraph, return it |
| `append(item)` | Append an existing `MutableParagraph` or `TableView` |
| `insert(index, item)` | Insert at index |
| `remove(index)` | Remove item at index |
| `clear()` | Remove all items |
| `len(doc.paragraphs)` | Number of body elements |
| `doc.paragraphs[i]` | Access by index |

## RunCollection reference

`para.runs` is a `RunCollection` — an ordered, mutable list of runs.

| Method | Description |
|---|---|
| `add_text(text, bold, italic, underline, strike, font_name, font_size, color, highlight, vertical_align)` | Create and append a `MutableRun`, return it |
| `append(run)` | Append an existing `MutableRun` or `MutableImageRun` |
| `insert(index, run)` | Insert at index |
| `remove(index)` | Remove run at index |
| `clear()` | Remove all runs |

## Tables (read-only in v0.2)

Tables parsed from DOCX or HTML are exposed as `TableView` objects. Full table editing is planned for v0.4.

```python
from docwow.api import TableView

for item in doc.paragraphs:
    if isinstance(item, TableView):
        print(f"{len(item)} rows, style: {item.style_id}")
        for row in item:
            for cell in row:
                print(f"  [{cell.col_span}x{cell.row_span}] {cell.get_text()!r}")
```
