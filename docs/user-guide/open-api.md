# Working with the Document Model

`docwow.open()` parses any supported input into a `Document` model, giving you programmatic access to the document's structure before converting or rendering.

## Opening a document

```python
import docwow

# From a DOCX file path
doc = docwow.open("report.docx")

# From DOCX bytes
with open("report.docx", "rb") as f:
    doc = docwow.open(f.read())

# From a docwow HTML string
html = docwow.to_html("report.docx")
doc = docwow.open(html)
```

`open()` auto-detects the input type: DOCX files (by extension or ZIP magic bytes `PK`) are parsed by the DOCX parser; anything else is treated as a docwow HTML string.

## The Document model

```python
from docwow.models.document import Document
from docwow.models.paragraph import Paragraph, TextRun, ImageRun
from docwow.models.table import Table

doc = docwow.open("report.docx")

# Page geometry (all in points)
print(doc.page_width_pt)      # e.g. 595.28
print(doc.margin_top_pt)      # e.g. 72.0

# Body elements — paragraphs and tables, in document order
for element in doc.body:
    if isinstance(element, Paragraph):
        for run in element.runs:
            if isinstance(run, TextRun):
                print(run.text)
    elif isinstance(element, Table):
        for row in element.rows:
            for cell in row.cells:
                print(f"  cell with {len(cell.paragraphs)} paragraph(s)")
```

## Inspecting styles

```python
for style in doc.styles:
    print(style.style_id, style.name)
    if style.run_fmt and style.run_fmt.font_size_pt:
        print(f"  font size: {style.run_fmt.font_size_pt}pt")
```

## Inspecting lists

```python
from docwow.models.paragraph import Paragraph

for element in doc.body:
    if isinstance(element, Paragraph) and element.list_info:
        info = element.list_info
        print(f"List {info.num_id}, level {info.level}: {element.runs[0].text}")
```

## Building a Document from scratch

All model classes are immutable frozen dataclasses. Build them top-down:

```python
from docwow.models.document import Document
from docwow.models.paragraph import Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting

doc = Document(
    body=(
        Paragraph(
            runs=(
                TextRun(text="Hello, "),
                TextRun(text="world!", formatting=RunFormatting(bold=True)),
            ),
            formatting=ParagraphFormatting(alignment="center"),
        ),
    ),
    styles=(),
    numbering=(),
    page_width_pt=595.28,
    page_height_pt=841.89,
    margin_top_pt=72.0,
    margin_right_pt=72.0,
    margin_bottom_pt=72.0,
    margin_left_pt=72.0,
)

html = docwow.render_document(doc)
data = docwow.write_docx(doc, target="hello.docx")
```

## Model reference

| Class | Module | Description |
|---|---|---|
| `Document` | `docwow.models.document` | Top-level container |
| `Paragraph` | `docwow.models.paragraph` | A paragraph with runs |
| `TextRun` | `docwow.models.paragraph` | Inline text with formatting |
| `ImageRun` | `docwow.models.paragraph` | Inline image |
| `Table` | `docwow.models.table` | Table |
| `TableRow` | `docwow.models.table` | Table row |
| `TableCell` | `docwow.models.table` | Table cell |
| `Style` | `docwow.models.styles` | Named Word style |
| `ParagraphFormatting` | `docwow.models.styles` | Paragraph-level formatting |
| `RunFormatting` | `docwow.models.styles` | Run-level formatting |
| `ListInfo` | `docwow.models.lists` | Links a paragraph to a list |
| `NumberingDefinition` | `docwow.models.lists` | A list's numbering definition |
| `InlineImage` | `docwow.models.image` | Image metadata + binary data |
