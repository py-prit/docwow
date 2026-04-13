# Architecture

## Pipeline overview

docwow is structured as a three-layer pipeline with an internal Document model as the source of truth:

```
DOCX file
    │
    ▼
┌─────────────────┐
│  docwow/parser/ │  DOCX XML → Document model
│  (docx_parser)  │  lxml.etree parses OOXML; EMU → pt unit conversion
└────────┬────────┘
         │  Document (frozen dataclasses)
         ▼
┌──────────────────────┐        ┌──────────────────────┐
│ docwow/renderer/     │        │ docwow/writer/        │
│ (html_renderer)      │        │ (docx_writer)         │
│ Document → HTML      │        │ Document → DOCX ZIP   │
│ CSS + data-dw-* attrs│        │ lxml.etree builds XML │
└──────────┬───────────┘        └──────────────────────┘
           │  HTML string                ▲
           ▼                             │
┌─────────────────────┐                 │ Document (frozen dataclasses)
│ docwow/html_parser/ │─────────────────┘
│ (html_parser)       │  docwow HTML → Document model
│ lxml.html parses    │  data-dw-* attrs → model fields
└─────────────────────┘
```

The pipeline is strictly unidirectional at each stage. No layer reaches into another layer's internals.

## Programmatic API layer (v0.2)

`docwow/api/` sits above the pipeline as a mutable wrapper layer. It is the primary interface for user code — `docwow.open()` returns a `DocumentWrapper`, not a raw `Document`.

```
                    ┌──────────────────────────────────────┐
                    │           docwow/api/                │
                    │  DocumentWrapper                     │
                    │  ├── ParagraphCollection             │  ◄── user code
                    │  │   ├── MutableParagraph            │
                    │  │   │   └── RunCollection           │
                    │  │   │       └── MutableRun          │
                    │  │   ├── MutableListItem             │
                    │  │   ├── MutableImage                │
                    │  │   └── MutableTable               │
                    │  │       └── MutableTableRow        │
                    │  │           └── MutableTableCell   │
                    └──────────────┬───────────────────────┘
                                   │  _to_frozen()
                                   ▼
                        Document (frozen dataclasses)
                                   │
                    ┌──────────────┴───────────────┐
                    ▼                               ▼
             docwow/renderer/              docwow/writer/
             HTML output                   DOCX output
```

The API layer converts to frozen models on demand via `_to_frozen()` — only when `save()`, `to_bytes()`, or `to_html()` is called. The frozen pipeline is never exposed to user code directly.

## Key design decisions

### Frozen dataclasses for the Document model

All model classes use `@dataclass(frozen=True)`. This means:

- Models are immutable — once parsed, a Document cannot be accidentally modified
- Safe to share across threads without locking
- Pipeline stages produce new models rather than mutating existing ones
- Equality comparison works correctly (`==` compares field values, not identity)

### data-dw-* attributes for round-trip fidelity

Rather than inferring Word semantics from HTML CSS (which is lossy), docwow embeds the original Word metadata directly in HTML attributes. For example:

- `data-dw-indent-left="36.0"` carries the exact point value even though CSS `padding-left` would round it
- `data-dw-v-merge-continue="true"` marks cells that are visually hidden by `rowspan` but must be present in DOCX XML
- `data-dw-num-id="1"` links list paragraphs to their numbering definition across the document

### Units: always points in the model

Word XML uses multiple unit systems (EMU for images, twips for paragraph measurements, half-points for font sizes). The model stores everything in points. Conversions happen at format boundaries:

- DOCX parser: EMU → pt, twips → pt, half-points → pt
- HTML renderer: pt → CSS (`pt` unit in CSS, or `px` for inline dimensions)
- DOCX writer: pt → twips, pt → EMU, pt → half-points

### Unknown elements are skipped

The DOCX parser silently ignores XML elements it doesn't recognise. This is intentional: real-world DOCX files contain hundreds of optional elements; attempting to parse all of them would be brittle. A future version will add a passthrough mechanism for lossless handling of unknown content.

## Module map

```
docwow/
├── __init__.py              Public API (open, to_html, to_docx, ...)
├── api/                     Programmatic API — mutable wrapper layer
│   ├── document.py          DocumentWrapper
│   ├── paragraph.py         MutableParagraph, ParagraphCollection
│   ├── run.py               MutableRun, MutableImageRun, RunCollection
│   ├── list_item.py         MutableListItem
│   ├── image.py             MutableImage
│   ├── table.py             MutableTable, MutableTableRow, MutableTableCell
│   └── _convert.py          DocumentWrapper → frozen Document (internal)
├── models/                  Internal Document model (frozen dataclasses)
│   ├── document.py          Document — top-level container
│   ├── paragraph.py         Paragraph, TextRun, ImageRun
│   ├── table.py             Table, TableRow, TableCell
│   ├── lists.py             ListInfo, ListLevel, NumberingDefinition
│   ├── image.py             InlineImage
│   └── styles.py            Style, ParagraphFormatting, RunFormatting
├── parser/                  DOCX XML → Document model
│   ├── docx_parser.py       ZIP unpacking, orchestration
│   ├── body_parser.py       <w:body> → paragraphs and tables
│   ├── style_parser.py      <w:styles> → Style objects
│   ├── numbering_parser.py  <w:numbering> → NumberingDefinition objects
│   └── image_parser.py      Relationship lookup + image bytes extraction
├── renderer/                Document model → HTML
│   ├── html_renderer.py     Orchestration, <html>/<head>/<body> wrapper
│   ├── css_generator.py     <style> block generation
│   ├── paragraph_renderer.py <p> + <span> elements
│   ├── table_renderer.py    <table>/<tr>/<td> elements
│   ├── list_renderer.py     <ul>/<ol>/<li> elements
│   └── image_renderer.py    <img> with base64 data URI
├── html_parser/             docwow HTML → Document model
│   ├── html_parser.py       Orchestration, page geometry, numbering reconstruction
│   ├── paragraph_parser.py  <p class="dw-p"> → Paragraph
│   └── table_parser.py      <table class="dw-table"> → Table
├── writer/                  Document model → DOCX ZIP
│   ├── docx_writer.py       ZIP assembly, image deduplication
│   ├── document_writer.py   word/document.xml
│   ├── styles_writer.py     word/styles.xml
│   ├── numbering_writer.py  word/numbering.xml
│   ├── parts_writer.py      [Content_Types].xml, .rels, settings.xml
│   └── _xml.py              Namespace constants, lxml helpers, unit conversions
└── utils/
    ├── units.py             pt ↔ CSS unit conversion
    ├── color.py             Theme color resolution
    └── xml_utils.py         OOXML namespace helpers
```

## OOXML notes

A DOCX file is a ZIP archive containing XML files following the Office Open XML standard (ECMA-376). Key parts:

| ZIP path | Content |
|---|---|
| `word/document.xml` | Document body (paragraphs, tables, images) |
| `word/styles.xml` | Named style definitions |
| `word/numbering.xml` | List/numbering definitions |
| `word/settings.xml` | Document settings |
| `word/media/` | Embedded images |
| `word/_rels/document.xml.rels` | Relationship file (links image references to media files) |
| `[Content_Types].xml` | MIME types for each part |
| `_rels/.rels` | Root relationships |

docwow uses `lxml.etree` throughout for XML parsing and generation. Clark notation (`{namespace}localname`) is used for all element and attribute names.
