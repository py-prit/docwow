# Bookmarks

Bookmarks are named anchors inside a Word document. They let you create in-document hyperlinks that jump the reader to a specific location — for example, `#introduction` linking to the start of a section.

docwow parses, renders, and round-trips bookmarks through the full pipeline.

## Reading bookmarks from DOCX

When you open a DOCX file, each `w:bookmarkStart` element becomes a `MutableBookmark` run:

```python
import docwow
from docwow.api.run import MutableBookmark

doc = docwow.open("document.docx")

for para in doc.paragraphs:
    for run in para.runs:
        if isinstance(run, MutableBookmark):
            print(run.name)  # e.g. "introduction", "chapter2"
```

## Adding bookmarks with the programmatic API

Use `runs.add_bookmark(name)` to insert a bookmark anchor at any point in a paragraph:

```python
from docwow.api.document import DocumentWrapper

doc = DocumentWrapper()

# Paragraph with a named bookmark anchor
heading = doc.paragraphs.add_paragraph()
heading.runs.add_bookmark("introduction")
heading.runs.add_text("Introduction", bold=True)

# Paragraph with a hyperlink pointing to the bookmark
body = doc.paragraphs.add_paragraph()
body.runs.add_text("Jump to ")
body.runs.add_hyperlink("Introduction", "#introduction")

doc.to_docx("output.docx")
```

`add_bookmark()` returns the `MutableBookmark` so you can update the name later:

```python
bm = heading.runs.add_bookmark("temp")
bm.set_name("introduction")   # rename
```

## HTML output

Bookmarks render as zero-width `<a id="…">` anchors:

```html
<a id="introduction"
   class="dw-bookmark"
   data-dw-bookmark="introduction"></a>
```

An anchor hyperlink `#introduction` in the same document resolves to this element in the browser.

## Round-trip fidelity

Bookmarks survive a full DOCX → HTML → DOCX round-trip. The `w:bookmarkStart` / `w:bookmarkEnd` pair is reconstructed during the write phase; each bookmark receives a unique integer `w:id` automatically.

## Limitations

- **Internal Word bookmarks are skipped.** Word silently inserts bookmarks whose names start with `_` (such as `_GoBack`) for its own navigation purposes. docwow discards these on parse.
- **Bookmark ranges are not preserved.** A Word bookmark can span a range of text, but docwow models it as a single point anchor (the start position). The range end is synthesised immediately after the start on write, making all docwow bookmarks zero-width.
- **Duplicate bookmark names.** Word allows duplicate bookmark names in theory; docwow preserves all of them, but in-browser anchor resolution will jump to the first matching `id`.
