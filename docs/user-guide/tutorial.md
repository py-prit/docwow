# Tutorial: Build and Read Documents

This tutorial covers two things:

1. **Reading an existing document** — iterating body elements, reading paragraph formatting and run properties
2. **Building a document from scratch** — a complete company report covering every major feature

## Reading an existing document

### Open and iterate

```python
import docwow
from docwow.api import MutableParagraph, MutableRun, MutableImageRun, MutableHyperlink, MutableBookmark, MutableTable

doc = docwow.open("report.docx")

for item in doc.paragraphs:
    if isinstance(item, MutableTable):
        print(f"Table: {len(item)} rows × {len(item[0])} cols")
        for row in item:
            for cell in row:
                print(f"  {cell.get_text()!r}")
    else:
        print(f"Para [{item.style_id}]: {item.get_text()!r}")
```

### Read paragraph formatting

```python
para = doc.paragraphs[0]

# Text and style
print(para.get_text())
print(para.style_id)          # e.g. "Heading1"
print(para.alignment)         # "left", "center", "right", "justify", or None

# Indentation
print(para.indent_left_pt)
print(para.indent_right_pt)
print(para.indent_first_line_pt)

# Spacing
print(para.space_before_pt)
print(para.space_after_pt)
print(para.line_spacing_pt)   # None = automatic

# Pagination flags
print(para.keep_together)
print(para.keep_with_next)
print(para.page_break_before)
```

### Read run properties

```python
for run in para.runs:
    if isinstance(run, MutableRun):
        print(run.get_text(), run.bold, run.italic, run.font_size, run.color)
    elif isinstance(run, MutableImageRun):
        print(f"Image {run.width_pt}×{run.height_pt}pt, alt={run.alt_text!r}")
    elif isinstance(run, MutableHyperlink):
        print(f"Link: {run.get_text()!r} → {run.url}")
```

### Read and edit tables

```python
from docwow.api import MutableTable

for item in doc.paragraphs:
    if isinstance(item, MutableTable):
        print(f"Table: {len(item)} rows × {len(item[0])} cols")
        for row in item:
            for cell in row:
                print(f"  {cell.get_text()!r}")
```

Edit a cell's content:

```python
table = next(item for item in doc.paragraphs if isinstance(item, MutableTable))

# Edit existing cell text
table[0][0].paragraphs[0].set_text("Updated header")

# Add a new paragraph to a cell
table[1][2].paragraphs.add_paragraph("new content")

# Add a new row
row = table.add_row(num_cells=3)
row[0].paragraphs.add_paragraph("New row, col 1")
```

### Edit what you read

```python
# Update formatting on an existing paragraph
para = doc.paragraphs[0]
para.set_alignment("center").set_style("Heading1")

# Update a specific run
run = para.runs[0]
if isinstance(run, MutableRun):
    run.set_bold(True).set_color("1A237E")

# Resize an image in-place
for run in para.runs:
    if isinstance(run, MutableImageRun):
        run.set_width_pt(300.0).set_height_pt(150.0).set_alt_text("Updated chart")

doc.save("updated.docx")
```

---

## Building a document from scratch

## 1. Setup

```python
import docwow
from docwow.api import DocumentWrapper
```

## 2. Create the document and set page geometry

```python
doc = DocumentWrapper()

# A4 paper, 2.5 cm margins (≈ 70.9 pt)
doc.set_page_size(595.28, 841.89)
doc.set_margins(top_pt=70.9, bottom_pt=70.9, left_pt=70.9, right_pt=70.9)
```

## 3. Header and footer

Add a company name to the header and a page number to the footer before writing any body content.

```python
# Header: company name, right-aligned
hdr = doc.header
h_para = hdr.paragraphs.add_paragraph()
h_para.set_alignment("right")
h_para.runs.add_text("Acme Corp", italic=True)

# Footer: "Page N of M", centred
ftr = doc.footer
f_para = ftr.paragraphs.add_paragraph()
f_para.set_alignment("center")
f_para.runs.add_text("Page ")
f_para.runs.add_page_number()           # PAGE field
f_para.runs.add_text(" of ")
f_para.runs.add_page_number("NUMPAGES") # NUMPAGES field
```

In HTML the footer paragraph is hidden (it's meaningless without real pagination) but the fields are preserved in the DOM so a round-trip back to DOCX restores them. In Word, the footer shows "Page 1 of 3" etc.

## 4. Title and introduction

```python
doc.paragraphs.add_paragraph("Q2 2025 Performance Report", style_id="Heading1")

intro = doc.paragraphs.add_paragraph()
intro.runs.add_text("Revenue grew by ")
intro.runs.add_text("18%", bold=True, color="2E7D32")
intro.runs.add_text(" compared to the same quarter last year. Full details are available on the ")
intro.runs.add_hyperlink("company intranet", "https://intranet.acme.example")
intro.runs.add_text(".")
```

## 5. Bulleted highlights

```python
doc.paragraphs.add_paragraph("Highlights", style_id="Heading2")

num_id = doc.add_numbering_definition(num_fmt="bullet")
doc.paragraphs.add_list_item("Record software revenue: $4.2 M", num_id=num_id)
doc.paragraphs.add_list_item("New enterprise accounts: 37", num_id=num_id)
doc.paragraphs.add_list_item("Churn rate below 2% for third consecutive quarter", num_id=num_id)
doc.paragraphs.add_list_item("EMEA expansion", num_id=num_id)
doc.paragraphs.add_list_item("UK: 12 new customers", num_id=num_id, level=1)
doc.paragraphs.add_list_item("Germany: 8 new customers", num_id=num_id, level=1)
```

## 6. Page break before the next section

```python
doc.paragraphs.add_page_break()
```

In HTML this becomes `<div class="dw-page-break" data-dw-page="2">` — invisible but preserved for the round-trip.

## 7. Regional breakdown table

```python
doc.paragraphs.add_paragraph("Regional Breakdown", style_id="Heading2")

# Build a 3×3 table from scratch
tbl = doc.paragraphs.add_table(rows=3, cols=3, style_id="TableGrid")

# Header row — bold
headers = ["Region", "Q2 Revenue", "Growth"]
for col_idx, text in enumerate(headers):
    tbl[0][col_idx].paragraphs.add_paragraph().runs.add_text(text, bold=True)

# Data rows
data = [
    ("EMEA",  "$1.8 M", "+22%"),
    ("AMER",  "$1.6 M", "+14%"),
]
for row_idx, row_data in enumerate(data, start=1):
    for col_idx, text in enumerate(row_data):
        tbl[row_idx][col_idx].paragraphs.add_paragraph(text)
```

## 8. Image

```python
doc.paragraphs.add_paragraph("Revenue Chart", style_id="Heading2")

with open("chart.png", "rb") as f:
    img_data = f.read()

doc.paragraphs.add_image(
    img_data,
    content_type="image/png",
    width_pt=400.0,
    height_pt=200.0,
    alt_text="Q2 Revenue Chart",
)
```

Images are embedded as base64 data URIs in HTML and restored as binary files in DOCX.

## 9. Numbered action items

```python
doc.paragraphs.add_paragraph("Next Steps", style_id="Heading2")

steps_id = doc.add_numbering_definition(num_fmt="decimal")
doc.paragraphs.add_list_item("Present results to the board by 15 July", num_id=steps_id)
doc.paragraphs.add_list_item("Finalise EMEA hiring plan", num_id=steps_id)
doc.paragraphs.add_list_item("Update sales forecast model", num_id=steps_id)
```

## 10. Footnotes

```python
# Create a footnote body
fn = doc.add_footnote()
fn.paragraphs.add_paragraph("Source: Internal Q2 analytics dashboard.")

# Add a reference marker inside a body paragraph
para = doc.paragraphs.add_paragraph()
para.runs.add_text("All revenue figures are reported in USD")
para.runs.add_footnote_ref(note_id=fn.note_id)
para.runs.add_text(".")
```

## 11. Save to DOCX

```python
doc.save("q2_report.docx")
```

Open `q2_report.docx` in Word and verify:

- Header shows "Acme Corp" right-aligned on every page
- Footer shows "Page N of M"
- A page break separates the introduction from the regional breakdown
- Bullet and numbered lists are formatted correctly
- The image is embedded
- The footnote appears at the bottom of the relevant page

## 12. Convert to HTML

```python
# Standard HTML — for browser viewing or embedding in a web app
html = doc.to_html()
with open("q2_report.html", "w", encoding="utf-8") as f:
    f.write(html)

# Page-view HTML — adds @media print CSS for correct paper size when printing or exporting to PDF
html_pv = doc.to_html(page_view=True)
with open("q2_report_print.html", "w", encoding="utf-8") as f:
    f.write(html_pv)
```

Open `q2_report.html` in a browser and verify:

- Header text is visible above the document
- Footer is hidden (page-number-only paragraph is `display:none`)
- Body text, lists, and hyperlink all render correctly
- The page break div is invisible

## 13. Round-trip HTML → DOCX

```python
# Read the HTML back and convert to DOCX
with open("q2_report.html", "r", encoding="utf-8") as f:
    html = f.read()

rt_bytes = docwow.to_docx(html)
with open("q2_report_restored.docx", "wb") as f:
    f.write(rt_bytes)
```

Open `q2_report_restored.docx` in Word and verify that the header, footer page number fields, page break, text formatting, and hyperlink are all intact.

## Summary

| Feature | How |
|---|---|
| Page size / margins | `doc.set_page_size()`, `doc.set_margins()` |
| Header | `doc.header.paragraphs.add_paragraph()` |
| Footer with page number | `para.runs.add_page_number()` |
| Headings | `add_paragraph(text, style_id="Heading1")` |
| Mixed run formatting | `para.runs.add_text(text, bold=True, color="...")` |
| Hyperlink | `para.runs.add_hyperlink(text, url)` |
| Bullet list | `add_numbering_definition("bullet")` + `add_list_item()` |
| Numbered list | `add_numbering_definition("decimal")` + `add_list_item()` |
| Table | `doc.paragraphs.add_table(rows, cols, style_id="TableGrid")` |
| Edit table cell | `table[row][col].paragraphs.add_paragraph(text)` |
| Add table row | `table.add_row(num_cells=N)` |
| Page break | `doc.paragraphs.add_page_break()` |
| Image | `doc.paragraphs.add_image(data, content_type, width_pt, height_pt)` |
| Footnote | `doc.add_footnote()` + `para.runs.add_footnote_ref(note_id)` |
| Endnote | `doc.add_footnote(note_type="endnote")` + `add_footnote_ref(..., note_type="endnote")` |
| Bookmark | `para.runs.add_bookmark(name)` |
| Save DOCX | `doc.save("file.docx")` or `doc.to_bytes()` |
| Convert to HTML | `doc.to_html()` or `docwow.to_html("file.docx")` |
| Round-trip | `docwow.to_docx(html)` |
