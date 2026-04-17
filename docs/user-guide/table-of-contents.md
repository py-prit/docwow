# Table of Contents

docwow parses, renders, and round-trips Word Table of Contents (TOC) blocks through the full pipeline.

## How Word stores a TOC

In OOXML a TOC lives inside a `w:sdt` (structured document tag) element. The content is a series of paragraphs styled `TOCHeading` (the visible title) and `TOC1`–`TOC9` (entries at each depth level). Each entry is typically a `w:hyperlink` pointing to a `_Toc…` bookmark on the corresponding heading.

docwow detects a `w:sdt` as a TOC when:

1. `w:sdtPr/w:tag w:val` contains `"Table of Contents"`, or
2. `w:sdtPr/w:docPartObj/w:docPartGallery w:val` is `"Table of Contents"`, or
3. The content paragraphs use `TOCHeading` or `TOC1`–`TOC9` styles (style-based fallback).

## Reading a TOC from DOCX

When you open a DOCX file, each TOC block becomes a `MutableTableOfContents` in the document body:

```python
import docwow
from docwow.api.toc import MutableTableOfContents

doc = docwow.open("document.docx")

for item in doc.paragraphs:
    if isinstance(item, MutableTableOfContents):
        print(f"TOC title: {item.title}")
        for entry in item.entries:
            indent = "  " * (entry.level - 1)
            print(f"{indent}{entry.text}  →  {entry.url}")
```

## Creating a TOC with the programmatic API

Use `paragraphs.add_toc()` to insert a TOC into a document:

```python
from docwow.api.document import DocumentWrapper

doc = DocumentWrapper()

# Add a heading paragraph that will be the target
heading = doc.paragraphs.add_paragraph("Introduction")
heading.set_style("Heading1")

# Add a TOC
toc = doc.paragraphs.add_toc("Contents")
toc.add_entry("Introduction", url="#_Toc1", level=1)
toc.add_entry("Background", url="#_Toc2", level=2)
toc.add_entry("Methods", url="#_Toc3", level=1)

doc.to_docx("output.docx")
```

### Entry levels

TOC entries support 9 nesting depths (matching Word's `TOC1`–`TOC9` paragraph styles):

```python
toc = doc.paragraphs.add_toc()
toc.add_entry("Part I",          url="#_Toc1", level=1)
toc.add_entry("Chapter 1",       url="#_Toc2", level=2)
toc.add_entry("Section 1.1",     url="#_Toc3", level=3)
toc.add_entry("Part II",         url="#_Toc4", level=1)
```

### Entries without links

If a TOC entry has no anchor target, pass an empty URL:

```python
toc.add_entry("Appendix", url="", level=1)
```

The entry will be rendered as non-clickable text in HTML and written without a hyperlink in DOCX.

### Editing after creation

All setters are chainable:

```python
entry = toc.add_entry("temp")
entry.set_text("Introduction").set_url("#_Toc1").set_level(1)

toc.set_title("Table of Contents")
```

## HTML output

A TOC renders as a `<nav class="dw-toc">` element:

```html
<nav class="dw-toc" data-dw-toc="true" data-dw-toc-title="Contents">
  <p class="dw-toc-title">Contents</p>
  <ul class="dw-toc-list">
    <li class="dw-toc-entry dw-toc-level-1" data-dw-toc-level="1">
      <a class="dw-toc-link" href="#_Toc1">Introduction</a>
    </li>
    <li class="dw-toc-entry dw-toc-level-2" data-dw-toc-level="2">
      <a class="dw-toc-link" href="#_Toc2">Background</a>
    </li>
  </ul>
</nav>
```

Entry links navigate to the corresponding `<a id="…" class="dw-bookmark">` anchors placed by heading bookmarks. Level indentation is controlled by CSS classes `.dw-toc-level-1` through `.dw-toc-level-9`.

## Round-trip fidelity

TOC blocks survive a full DOCX → HTML → DOCX round-trip:

- The `data-dw-toc-title` attribute preserves the TOC heading text.
- Each `data-dw-toc-level` attribute preserves the entry depth.
- Anchor URLs are preserved via the `href` attribute on `<a class="dw-toc-link">`.
- On write, the TOC is reconstructed as a `w:sdt` with `TOCHeading` + `TOC1`–`TOC9` paragraphs and `w:hyperlink w:anchor="…"` elements.

## Bookmark target rule change

Prior to TOC support, docwow skipped **all** bookmarks whose names started with `_`. This version relaxes that rule: only `_GoBack` (Word's internal navigation bookmark) is skipped. `_Toc…` bookmarks — which are the anchor targets that TOC hyperlinks point to — are now preserved and round-tripped correctly.

## Limitations

- **TOC page numbers are not preserved.** Word's TOC entries include page number fields and tab leaders. docwow extracts only the heading text and the anchor URL; page numbers are dropped. On write the entry text is written without tab stops or page numbers.
- **No automatic TOC generation.** docwow does not scan headings and build a TOC automatically. You must supply the entries (text, url, level) explicitly, or let them come from a parsed DOCX.
- **Updating a TOC after editing.** If you programmatically add headings and then save to DOCX, the TOC entries you added will not reflect the updated heading text. Word will show a "TOC needs updating" prompt; click **Update Field** to regenerate.
