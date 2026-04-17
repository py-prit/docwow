# Programmatic API

`docwow.open()` returns a `DocumentWrapper` — a mutable object that lets you read, edit, and build Word documents in Python without touching XML.

For a full worked example covering every feature, see the [Tutorial](tutorial.md).

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

# Render to HTML
html = doc.to_html()

# Render to HTML with print/PDF page CSS
html = doc.to_html(page_view=True)
```

## Reading document content

### Iterating body elements

```python
from docwow.api import MutableParagraph, MutableTable

for item in doc.paragraphs:
    if isinstance(item, MutableTable):
        print(f"Table with {len(item)} rows")
    else:
        print(item.get_text())
```

### Reading paragraph text and formatting

```python
para = doc.paragraphs[0]
print(para.get_text())           # full text of all runs concatenated
print(para.style_id)             # e.g. "Heading1"
print(para.alignment)            # "left", "center", "right", "justify", or None
print(para.indent_left_pt)       # left indent in points
print(para.indent_right_pt)      # right indent in points
print(para.indent_first_line_pt) # first-line indent in points
print(para.space_before_pt)      # space before paragraph in points
print(para.space_after_pt)       # space after paragraph in points
print(para.line_spacing_pt)      # exact line spacing in points, or None for auto
print(para.keep_together)        # bool
print(para.keep_with_next)       # bool
print(para.page_break_before)    # bool
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

### Reading tables

```python
from docwow.api import MutableTable

for item in doc.paragraphs:
    if isinstance(item, MutableTable):
        print(f"Table: {len(item)} rows × {len(item[0])} cols")
        for row in item:
            for cell in row:
                print(cell.get_text())
```

Tables loaded from DOCX or HTML are fully mutable `MutableTable` objects — you can read, edit, add, and remove rows, cells, and content.

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
run.set_small_caps(True)               # lowercase letters rendered as smaller uppercase
run.set_all_caps(True)                 # all letters rendered as uppercase
run.set_font_name("Arial")
run.set_font_size(14.0)               # in points
run.set_color("FF0000")               # hex RGB, no '#'
run.set_highlight("yellow")
run.set_vertical_align("superscript") # or "subscript"
run.set_char_style("Strong")          # named Word character style; None to clear
```

### Paragraph-level formatting

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
para.set_shading("4472C4")   # solid background color (hex RGB)

from docwow.models.styles import TabStop
para.set_tab_stops((
    TabStop(position_pt=72.0, alignment="left"),
    TabStop(position_pt=216.0, alignment="right", leader="dot"),
))

# Cross-references — link to a named bookmark
para.runs.add_bookmark("my_target")          # define a target anchor
para.runs.add_cross_ref("my_target", "Section 1")  # insert a REF field
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

doc.save("report.docx")
```

## Hyperlinks

```python
para = doc.paragraphs.add_paragraph()
para.runs.add_text("Read the ")
para.runs.add_hyperlink("full documentation", "https://docwow.readthedocs.io")
para.runs.add_text(" for details.")
```

See [Hyperlinks](hyperlinks.md) for the full reference.

## Headers and footers

```python
# Header: company name
hdr = doc.header
para = hdr.paragraphs.add_paragraph()
para.runs.add_text("Acme Corp — Confidential")

# Footer: page number
ftr = doc.footer
para = ftr.paragraphs.add_paragraph()
para.runs.add_text("Page ")
para.runs.add_page_number()           # PAGE field
para.runs.add_text(" of ")
para.runs.add_page_number("NUMPAGES") # NUMPAGES field
```

The first-page and even-page slots are also available via `doc.header_first`, `doc.header_even`, `doc.footer_first`, `doc.footer_even`. Set `doc.title_pg = True` to activate the first-page slot.

See [Headers, Footers & Page Numbers](headers-footers.md) for the full reference.

## Page breaks

```python
doc.paragraphs.add_paragraph("End of section one.")
doc.paragraphs.add_page_break()
doc.paragraphs.add_paragraph("Start of section two.")
```

## Working with lists

```python
# Bullet list
num_id = doc.add_numbering_definition(num_fmt="bullet")
doc.paragraphs.add_list_item("First point", num_id=num_id, level=0)
doc.paragraphs.add_list_item("Sub-point", num_id=num_id, level=1)
doc.paragraphs.add_list_item("Second point", num_id=num_id, level=0)

# Numbered list
num_id2 = doc.add_numbering_definition(num_fmt="decimal")
doc.paragraphs.add_list_item("Step one", num_id=num_id2)
doc.paragraphs.add_list_item("Step two", num_id=num_id2)
```

### `add_numbering_definition(num_fmt)`

Registers a new list style and returns its `num_id`. Pass that `num_id` when adding list items.

```
num_fmt options: "bullet", "decimal", "lowerLetter", "upperLetter", "lowerRoman", "upperRoman"
```

## Tables

### Building a table from scratch

```python
# 3-row × 3-col table
tbl = doc.paragraphs.add_table(rows=3, cols=3, style_id="TableGrid")

# Fill header row with bold text
for col, heading in enumerate(["Region", "Q2 Revenue", "Growth"]):
    tbl[0][col].paragraphs.add_paragraph().runs.add_text(heading, bold=True)

# Fill data rows
tbl[1][0].paragraphs.add_paragraph("EMEA")
tbl[1][1].paragraphs.add_paragraph("$1.8 M")
tbl[1][2].paragraphs.add_paragraph("+22%")
```

### Adding and removing rows

```python
# Append a new row at the end
row = tbl.add_row(num_cells=3, height_pt=20.0)
row[0].paragraphs.add_paragraph("New row")

# Insert a row at position 1
from docwow.api import MutableTableRow, MutableTableCell
new_row = MutableTableRow(cells=[MutableTableCell() for _ in range(3)])
tbl.insert(1, new_row)

# Remove the last row
tbl.remove(len(tbl) - 1)
```

### Editing cells from an existing document

```python
from docwow.api import MutableTable

for item in doc.paragraphs:
    if isinstance(item, MutableTable):
        # Edit existing cell
        item[0][0].paragraphs[0].set_text("Updated header")
        # Add a new paragraph inside a cell
        item[1][2].paragraphs.add_paragraph("extra note")
        break
```

### Cell properties

```python
cell = tbl[0][0]
cell.set_width_pt(150.0)      # cell width
cell.set_col_span(2)          # merge across 2 columns
cell.set_row_span(1)          # row span
cell.set_shading("ED7D31")    # background color (hex RGB); None to clear
print(cell.col_span, cell.row_span, cell.width_pt, cell.shading)
```

### Table properties

```python
tbl.set_width_pt(450.0)
tbl.set_style("TableGrid")
tbl.set_col_widths_pt([150.0, 150.0, 150.0])
print(tbl.width_pt, tbl.style_id, tbl.col_widths_pt)
```

## Footnotes and endnotes

### Reading footnotes from an existing document

```python
from docwow.api import MutableFootnote, MutableFootnoteRef

# All footnote bodies
for note in doc.footnotes:
    print(f"Footnote {note.note_id}: {note.get_text()}")

# Endnotes
for note in doc.endnotes:
    print(f"Endnote {note.note_id}: {note.get_text()}")

# Find footnote references in the body
from docwow.api import MutableParagraph
for item in doc.paragraphs:
    if isinstance(item, MutableParagraph):
        for run in item.runs:
            if isinstance(run, MutableFootnoteRef):
                print(f"Footnote reference to note {run.note_id}")
```

### Adding footnotes programmatically

```python
# Register a footnote body — auto-assigns an ID
note = doc.add_footnote()
note.paragraphs.add_paragraph("This is the footnote text.")

# Place the marker in the body paragraph
para = doc.paragraphs.add_paragraph("See the attached reference")
para.runs.add_footnote_ref(note_id=note.note_id)

# Endnotes use the same API with note_type="endnote"
en = doc.add_footnote(note_type="endnote")
en.paragraphs.add_paragraph("This appears in the endnote section.")
para2 = doc.paragraphs.add_paragraph("Another referenced paragraph")
para2.runs.add_footnote_ref(note_id=en.note_id, note_type="endnote")
```

Footnote IDs are assigned automatically and sequentially within each note type. Footnote and endnote IDs are independent — both start at 1.

## Bookmarks

### Reading bookmarks from an existing document

```python
from docwow.api import MutableBookmark

for item in doc.paragraphs:
    for run in item.runs:
        if isinstance(run, MutableBookmark):
            print(run.name)  # e.g. "introduction", "chapter2"
```

### Adding bookmarks programmatically

```python
# Place a named anchor at the start of a paragraph
heading = doc.paragraphs.add_paragraph()
heading.runs.add_bookmark("introduction")
heading.runs.add_text("Introduction", bold=True)

# Add an in-document hyperlink pointing to the bookmark
body = doc.paragraphs.add_paragraph()
body.runs.add_text("Jump to ")
body.runs.add_hyperlink("Introduction", "#introduction")
```

`add_bookmark()` returns the `MutableBookmark` so you can rename it later:

```python
bm = heading.runs.add_bookmark("temp-name")
bm.set_name("introduction")
```

## Comments

Use `doc.add_comment()` to create a comment body, then `para.runs.add_comment_ref()` to place the reference marker in the text.

```python
from docwow.api import MutableComment

# Create a comment with text, author, date
comment = doc.add_comment(
    author="Alice",
    text="Revenue figure needs verification.",
    date="2025-07-10T09:00:00Z",
    initials="A",
)

# Place a reference marker at the relevant point in the body
para = doc.paragraphs.add_paragraph()
para.runs.add_text("Revenue grew by 18%")
para.runs.add_comment_ref(comment_id=comment.comment_id)
para.runs.add_text(" year-on-year.")
```

### Reading comments from an existing document

```python
from docwow.api import MutableComment

for comment in doc.comments:
    print(f"[{comment.comment_id}] {comment.author}: {comment.get_text()}")
```

### Adding multi-paragraph comment content

```python
comment = doc.add_comment(author="Bob")
comment.paragraphs.add_paragraph("First paragraph of comment.")
comment.paragraphs.add_paragraph("Second paragraph with more detail.")
```

### Setters

`add_comment()` returns a `MutableComment` with chainable setters:

```python
comment.set_author("Carol").set_date("2025-07-11T08:00:00Z").set_initials("C")
```

In HTML, comment references render as superscript `[N]` anchors with a CSS-only hover popup showing the author, date, and comment text — similar to how Word shows comments in a side pane when you hover. The comment bodies are also stored in a hidden `<section class="dw-comments">` block (invisible in the browser) that the HTML parser reads when round-tripping back to DOCX. In DOCX they are stored in `word/comments.xml` with matching `w:commentRangeStart`, `w:commentRangeEnd`, and `w:commentReference` elements.

## Track Changes

Use `para.runs.add_insertion()` and `para.runs.add_deletion()` to record reviewer edits, or read them from a parsed DOCX that has tracked changes enabled.

```python
from docwow.api import MutableTrackedChange

# Build tracked changes programmatically
para = doc.paragraphs.add_paragraph()
para.runs.add_text("The figure was ")
para.runs.add_deletion("$3.8 M", author="Alice", date="2025-07-10T09:00:00Z")
para.runs.add_insertion("$4.2 M", author="Alice", date="2025-07-10T09:00:00Z")

# Read tracked changes from an existing document
for item in doc.paragraphs:
    for run in item.runs:
        if isinstance(run, MutableTrackedChange):
            action = "inserted" if run.change_type == "insert" else "deleted"
            print(f"{run.author} {action}: {run.get_text()!r}")
```

In HTML, insertions render as `<ins class="dw-ins">` (green underline) and deletions as `<del class="dw-del">` (red strikethrough) with `data-dw-author`, `data-dw-date`, and `data-dw-change-id` attributes for lossless round-trip. Hovering over either element shows a popup with the author, date, and **Accept** / **Reject** buttons. Accepting or rejecting in the browser removes the track-change markup — if you then convert back to DOCX via `docwow.to_docx(html)`, the accepted/rejected state is preserved in the output. In DOCX they are stored as `w:ins` / `w:del` elements visible in Word's review pane.

`MutableTrackedChange` supports chainable setters:

```python
tc = para.runs.add_insertion("new text")
tc.set_author("Bob").set_date("2025-07-11T08:00:00Z")
```

## Table of Contents

Use `paragraphs.add_toc()` to insert a Table of Contents block, or read one from a parsed DOCX:

```python
from docwow.api.toc import MutableTableOfContents

# Read an existing TOC
for item in doc.paragraphs:
    if isinstance(item, MutableTableOfContents):
        print(item.title)
        for entry in item.entries:
            print(f"  {'  ' * (entry.level - 1)}{entry.text}")

# Create a new TOC
toc = doc.paragraphs.add_toc("Contents")
toc.add_entry("Introduction", url="#_Toc1", level=1)
toc.add_entry("Background",   url="#_Toc2", level=2)
toc.add_entry("Methods",      url="#_Toc3", level=1)
```

`add_toc()` returns a `MutableTableOfContents` with chainable setters:

```python
toc.set_title("Table of Contents")
entry = toc.add_entry("Results")
entry.set_url("#_Toc4").set_level(1)
```

See [Table of Contents](table-of-contents.md) for the full guide.

## Images

```python
with open("logo.png", "rb") as f:
    img_data = f.read()

doc.paragraphs.add_image(
    img_data,
    content_type="image/png",
    width_pt=200.0,
    height_pt=100.0,
    alt_text="Company logo",
)
```

To edit an image run parsed from an existing document:

```python
from docwow.api import MutableImageRun

for run in para.runs:
    if isinstance(run, MutableImageRun):
        run.set_width_pt(300.0)          # resize
        run.set_height_pt(150.0)
        run.set_alt_text("Updated chart")
        # or replace entirely:
        run.replace_image(new_bytes, "image/png", width_pt=300.0, height_pt=150.0)
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
| `add_page_break()` | Append an explicit page break, return it |
| `add_table(rows, cols, width_pt, style_id)` | Create and append a table, return it |
| `add_toc(title)` | Create and append a `MutableTableOfContents`, return it |
| `append(item)` | Append an existing `MutableParagraph`, `MutableTable`, `MutableTableOfContents`, or `PageBreak` |
| `insert(index, item)` | Insert at index |
| `remove(index)` | Remove item at index |
| `clear()` | Remove all items |
| `len(doc.paragraphs)` | Number of body elements |
| `doc.paragraphs[i]` | Access by index |

## RunCollection reference

`para.runs` is a `RunCollection` — an ordered, mutable list of runs.

| Method | Description |
|---|---|
| `add_text(text, bold, italic, ...)` | Create and append a `MutableRun`, return it |
| `add_hyperlink(text, url)` | Create and append a `MutableHyperlink`, return it |
| `add_bookmark(name)` | Create and append a `MutableBookmark` anchor, return it |
| `add_comment_ref(comment_id)` | Create and append a `MutableCommentRef` marker, return it |
| `add_insertion(text, author, date)` | Create and append a `MutableTrackedChange` insertion, return it |
| `add_deletion(text, author, date)` | Create and append a `MutableTrackedChange` deletion, return it |
| `add_footnote_ref(note_id, note_type)` | Create and append a `MutableFootnoteRef` marker, return it |
| `add_page_number(field_type)` | Create and append a `MutablePageNumberField`, return it |
| `append(run)` | Append an existing run |
| `insert(index, run)` | Insert at index |
| `remove(index)` | Remove run at index |
| `clear()` | Remove all runs |
