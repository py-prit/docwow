# Tutorial: Build and Read Documents

This tutorial covers two things:

1. **Reading an existing document** — iterating body elements, reading paragraph formatting and run properties
2. **Building a document from scratch** — a complete company report covering every major feature

## Reading an existing document

### Open and iterate

```python
import docwow
from docwow.api import MutableParagraph, MutableRun, MutableImageRun, MutableHyperlink, MutableBookmark, MutableTable, MutableTableOfContents

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

## 11. Bookmarks

Bookmarks mark a named location in the document body. Other elements (hyperlinks, TOC entries) can reference them as anchor targets.

```python
heading = doc.paragraphs.add_paragraph("Appendix A", style_id="Heading2")
heading.runs.add_bookmark("appendix-a")

# Internal anchor hyperlink pointing to that bookmark
para = doc.paragraphs.add_paragraph()
para.runs.add_text("See ")
para.runs.add_hyperlink("Appendix A", "#appendix-a")
para.runs.add_text(" for full details.")
```

In HTML the bookmark renders as `<a class="dw-bookmark" id="appendix-a"></a>` and the internal hyperlink becomes `<a href="#appendix-a">`.

## 12. Comments

Comments attach reviewer annotations to specific points in the document text.

```python
# Create a comment body
comment = doc.add_comment(
    author="Alice",
    text="Revenue figure needs verification.",
    date="2025-07-10T09:00:00Z",
    initials="A",
)

# Add a reference marker in a body paragraph
para = doc.paragraphs.add_paragraph()
para.runs.add_text("Revenue grew by 18%")
para.runs.add_comment_ref(comment_id=comment.comment_id)
para.runs.add_text(" year-on-year.")
```

In HTML the reference marker renders as an orange superscript `[1]` linking to a `<section class="dw-comments">` block at the bottom of the page. In DOCX the comment appears in the Word review pane (right-click to see it).

To read comments from an existing document:

```python
for comment in doc.comments:
    print(f"[{comment.comment_id}] {comment.author}: {comment.get_text()}")
```

## 13. Track Changes

Track changes records reviewer insertions and deletions. In HTML, insertions render as green underlined text and deletions as red strikethrough. Hovering over either shows a popup with the author, date, and **Accept** / **Reject** buttons — accepting or rejecting in the browser is preserved when converting back to DOCX. In DOCX they appear in Word's review pane.

```python
para = doc.paragraphs.add_paragraph()
para.runs.add_text("The revenue figure was ")
para.runs.add_deletion("$3.8 M", author="Alice", date="2025-07-10T09:00:00Z")
para.runs.add_insertion("$4.2 M", author="Alice", date="2025-07-10T09:00:00Z")
para.runs.add_text(" for the quarter.")
```

To read track changes from an existing document:

```python
from docwow.api import MutableTrackedChange

for item in doc.paragraphs:
    for run in item.runs:
        if isinstance(run, MutableTrackedChange):
            action = "inserted" if run.change_type == "insert" else "deleted"
            print(f"{run.author} {action}: {run.get_text()!r}")
```

## 14. Table of Contents

Build a TOC manually or point it at existing bookmark anchors. Each entry carries a display level (1–9) matching the heading depth.

```python
# Add TOC near the top of the document (before the body headings)
toc = doc.paragraphs.add_toc("Contents")
toc.add_entry("Introduction",        url="#intro",       level=1)
toc.add_entry("Highlights",          url="#highlights",  level=1)
toc.add_entry("  EMEA",              url="#emea",        level=2)
toc.add_entry("Regional Breakdown",  url="#regional",    level=1)
toc.add_entry("Next Steps",          url="#next-steps",  level=1)

# Then add matching bookmark anchors on the actual headings
intro_heading = doc.paragraphs.add_paragraph("Introduction", style_id="Heading1")
intro_heading.runs.add_bookmark("intro")
```

In HTML the TOC renders as a `<nav class="dw-toc">` element with clickable `<a>` links. In DOCX it becomes a `w:sdt` structured document tag with `TOC1`–`TOC9` styled paragraphs.

## 15. Save to DOCX

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
- TOC entries link to headings when clicked

## 16. Convert to HTML

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

## 17. Round-trip HTML → DOCX

```python
# Read the HTML back and convert to DOCX
with open("q2_report.html", "r", encoding="utf-8") as f:
    html = f.read()

rt_bytes = docwow.to_docx(html)
with open("q2_report_restored.docx", "wb") as f:
    f.write(rt_bytes)
```

Open `q2_report_restored.docx` in Word and verify that the header, footer page number fields, page break, text formatting, and hyperlink are all intact.

## 18. Converting arbitrary HTML to DOCX

Use `is_foreign_html=True` to convert HTML from any source — a CMS, rich text editor, web page, or email — into DOCX on a best-effort basis:

```python
import docwow

html = """
<h1>Quarterly Update</h1>
<p>Revenue grew by <b>18%</b> year-on-year.</p>
<p>Key highlights:</p>
<p>
  See the full report at
  <a href="https://example.com/report">example.com/report</a>.
</p>
<p>
  <span style="color: #C00000; font-weight: bold">Warning:</span>
  margins are under pressure in Q3.
</p>
"""

docwow.to_docx(html, "update.docx", is_foreign_html=True)
```

### What gets converted

Block structure maps to Word paragraphs, headings, and lists:

| HTML | Word |
|---|---|
| `<h1>`–`<h6>` | Heading 1–6 |
| `<p>`, `<div>` | Normal paragraph |
| `<blockquote>` | Indented paragraph |
| `<pre>` | Monospace paragraph |
| `<ul>` | Bulleted list (•/◦/▪ cycling per nesting level) |
| `<ol>` | Numbered list; `type="a/A/i/I"` and CSS `list-style-type` set format |
| `<li>` | List item; each nested list gets its own counter that restarts independently |
| `<table>` | Word table (TableGrid style, single-line borders) |
| `<thead>`, `<tbody>`, `<tfoot>` | Row groups — all rows included |
| `<th>` | Header cell, automatically bolded |
| `<td>` | Data cell; `colspan` and `rowspan` respected |
| `<colgroup>`/`<col>` | Column widths via CSS `width` |

Inline elements become character formatting within runs:

| HTML | Word |
|---|---|
| `<b>`, `<strong>` | Bold |
| `<i>`, `<em>` | Italic |
| `<u>` | Underline |
| `<s>`, `<del>` | Strikethrough |
| `<code>`, `<kbd>` | Courier New |
| `<mark>` | Yellow highlight |
| `<sub>` / `<sup>` | Subscript / superscript |
| `<a href="...">` | Hyperlink |
| `<span style="...">` | CSS-resolved formatting |

CSS properties on any element are applied to the corresponding run or paragraph:
`font-weight`, `font-style`, `font-size`, `font-family`, `color`,
`background-color`, `text-decoration`, `vertical-align`, `font-variant`,
`text-transform`, `text-align`, `margin-left`, `margin-top`, `margin-bottom`.

Formatting accumulates through nesting — `<b><i>text</i></b>` produces a bold+italic run.

### Handling warnings

When the converter encounters HTML it cannot represent in Word it emits a `DocwowConversionWarning` and continues:

```python
import warnings
import docwow

# Raise instead of warn (useful in CI)
warnings.filterwarnings("error", category=docwow.DocwowConversionWarning)

# Or silence entirely
docwow.suppress_warnings()
```

### External CSS and images

```python
# Download <link rel="stylesheet"> stylesheets before converting
docwow.to_docx(html, "out.docx", is_foreign_html=True, fetch_external_css=True)

# Download <img src="https://..."> images from remote URLs
docwow.to_docx(html, "out.docx", is_foreign_html=True, fetch_images=True)
```

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
| Comment | `doc.add_comment(author, text)` + `para.runs.add_comment_ref(comment_id)` |
| Track changes (insert) | `para.runs.add_insertion(text, author, date)` |
| Track changes (delete) | `para.runs.add_deletion(text, author, date)` |
| Table of Contents | `toc = doc.paragraphs.add_toc("Contents")` + `toc.add_entry(text, url, level)` |
| Save DOCX | `doc.save("file.docx")` or `doc.to_bytes()` |
| Convert to HTML | `doc.to_html()` or `docwow.to_html("file.docx")` |
| Round-trip | `docwow.to_docx(html)` |
| Arbitrary HTML → DOCX | `docwow.to_docx(html, is_foreign_html=True)` |
