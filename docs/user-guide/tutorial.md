# Tutorial: Build a Document from Scratch

This tutorial walks through every major docwow feature by building a complete Word document in Python — a short company report with a title, sections, formatted text, a list, a table (parsed from an existing file), an image, a hyperlink, a header, a footer with a page number, and a page break.

By the end you will have produced a `.docx` file and an `.html` file, and round-tripped the HTML back to DOCX.

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
from docwow.models.paragraph import PageBreak

doc.paragraphs.append(PageBreak())
```

In HTML this becomes `<div class="dw-page-break" data-dw-page="2">` — invisible but preserved for the round-trip.

## 7. Regional breakdown heading and table (from an existing DOCX)

If you have a DOCX file with a table you want to reuse, parse it and copy the content into the new document.  
For this tutorial we'll just show the pattern — replace `"existing.docx"` with your own file:

```python
doc.paragraphs.add_paragraph("Regional Breakdown", style_id="Heading2")

# Parse an existing document and copy its table content as plain text
existing = docwow.open("existing.docx")
for item in existing.paragraphs:
    from docwow.api import TableView
    if isinstance(item, TableView):
        for row in item:
            row_text = " | ".join(cell.get_text() for cell in row)
            doc.paragraphs.add_paragraph(row_text)
        break  # first table only
```

!!! note
    Table editing (adding/modifying cells) is not yet supported. Tables parsed from DOCX or HTML pass through unchanged.

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

## 10. Save to DOCX

```python
doc.save("q2_report.docx")
```

Open `q2_report.docx` in Word and verify:

- Header shows "Acme Corp" right-aligned on every page
- Footer shows "Page N of M"
- A page break separates the introduction from the regional breakdown
- Bullet and numbered lists are formatted correctly
- The image is embedded

## 11. Convert to HTML

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

## 12. Round-trip HTML → DOCX

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
| Page break | `doc.paragraphs.append(PageBreak())` |
| Image | `doc.paragraphs.add_image(data, content_type, width_pt, height_pt)` |
| Save DOCX | `doc.save("file.docx")` or `doc.to_bytes()` |
| Convert to HTML | `doc.to_html()` or `docwow.to_html("file.docx")` |
| Round-trip | `docwow.to_docx(html)` |
