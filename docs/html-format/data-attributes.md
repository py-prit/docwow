# data-dw-* Attributes

This page is the **authoritative specification** of the `data-dw-*` attribute system used by docwow's HTML output.

Every element in a docwow HTML document carries two things:

1. **CSS classes** — control visual appearance in the browser
2. **`data-dw-*` attributes** — carry Word metadata needed for lossless round-trip back to DOCX

If you are building a browser-based editor on top of docwow, you **must preserve all `data-dw-*` attributes** on every element. Stripping them will cause information loss when converting back to DOCX.

---

## Document container

```html
<div class="dw-document"
     data-dw-page-width="595.28"
     data-dw-page-height="841.89"
     data-dw-margin-top="72.0"
     data-dw-margin-right="72.0"
     data-dw-margin-bottom="72.0"
     data-dw-margin-left="72.0">
```

All dimension values are in **points (pt)**.

| Attribute | Type | Description |
|---|---|---|
| `data-dw-page-width` | float (pt) | Page width |
| `data-dw-page-height` | float (pt) | Page height |
| `data-dw-margin-top` | float (pt) | Top margin |
| `data-dw-margin-right` | float (pt) | Right margin |
| `data-dw-margin-bottom` | float (pt) | Bottom margin |
| `data-dw-margin-left` | float (pt) | Left margin |

---

## Paragraphs (`<p class="dw-p">`)

```html
<p class="dw-p dw-style-Normal"
   data-dw-style="Normal"
   data-dw-align="justify"
   data-dw-indent-left="36.0"
   data-dw-indent-right="0.0"
   data-dw-indent-first-line="18.0"
   data-dw-space-before="12.0"
   data-dw-space-after="6.0"
   data-dw-line-spacing="14.0"
   data-dw-page-break-before="true"
   data-dw-keep-together="true"
   data-dw-keep-with-next="true">
```

### Paragraph attributes

| Attribute | Type | Description |
|---|---|---|
| `data-dw-style` | string | Named Word style ID (e.g. `Normal`, `Heading1`) |
| `data-dw-align` | string | `left` \| `center` \| `right` \| `justify` |
| `data-dw-indent-left` | float (pt) | Left indent |
| `data-dw-indent-right` | float (pt) | Right indent |
| `data-dw-indent-first-line` | float (pt) | First-line indent. Negative value = hanging indent |
| `data-dw-space-before` | float (pt) | Space before paragraph |
| `data-dw-space-after` | float (pt) | Space after paragraph |
| `data-dw-line-spacing` | float (pt) | Exact line spacing. Absent = auto |
| `data-dw-page-break-before` | `"true"` | Forces a page break before this paragraph |
| `data-dw-keep-together` | `"true"` | Keep all lines of paragraph on same page |
| `data-dw-keep-with-next` | `"true"` | Keep this paragraph on same page as the next |

### List paragraph attributes

When a paragraph belongs to a list, it gains two additional attributes:

| Attribute | Type | Description |
|---|---|---|
| `data-dw-num-id` | string | Numbering definition ID (matches `data-dw-num-id` on the `<ul>`/`<ol>`) |
| `data-dw-level` | integer | List nesting level, 0-based |

---

## Runs (`<span class="dw-r">`)

```html
<span class="dw-r"
      data-dw-bold="true"
      data-dw-italic="true"
      data-dw-underline="true"
      data-dw-strike="true"
      data-dw-font="Arial"
      data-dw-size="14.0"
      data-dw-color="FF0000"
      data-dw-highlight="yellow"
      data-dw-valign="superscript">
  text content
</span>
```

| Attribute | Type | Description |
|---|---|---|
| `data-dw-bold` | `"true"` | Bold |
| `data-dw-italic` | `"true"` | Italic |
| `data-dw-underline` | `"true"` | Underline |
| `data-dw-strike` | `"true"` | Strikethrough |
| `data-dw-font` | string | Font family name |
| `data-dw-size` | float (pt) | Font size |
| `data-dw-color` | string | Font color as 6-digit hex, no `#` (e.g. `FF0000`) |
| `data-dw-highlight` | string | Highlight color name (e.g. `yellow`, `cyan`, `red`) |
| `data-dw-valign` | string | `superscript` \| `subscript` |

Boolean attributes (`data-dw-bold`, etc.) are only present when `true`; their absence means `false`.

Newlines within a run are represented as literal `\n` characters in the text content (preserved by `white-space: pre-wrap` in CSS).

---

## Tables (`<table class="dw-table">`)

```html
<table class="dw-table"
       data-dw-style="TableGrid"
       data-dw-width="360.0"
       data-dw-col-widths="120.0,120.0,120.0">
```

| Attribute | Type | Description |
|---|---|---|
| `data-dw-style` | string | Word table style ID |
| `data-dw-width` | float (pt) | Total table width |
| `data-dw-col-widths` | comma-separated floats (pt) | Width of each column, in order |

### Table cells (`<td class="dw-td">`)

```html
<td class="dw-td"
    colspan="2"
    data-dw-width="240.0"
    data-dw-v-merge-start="true">
```

| Attribute | Type | Description |
|---|---|---|
| `colspan` | integer | HTML standard colspan (column span) |
| `data-dw-width` | float (pt) | Cell width |
| `data-dw-v-merge-start` | `"true"` | This cell starts a vertical merge group |
| `data-dw-v-merge-continue` | `"true"` | This cell continues a vertical merge (is a continuation row) |

!!! note
    Vertically merged cells use the standard HTML `rowspan` attribute for visual rendering,
    but `data-dw-v-merge-start` / `data-dw-v-merge-continue` are also written so the
    round-trip reconstructs Word's `<w:vMerge>` elements exactly.

---

## Lists (`<ul>` / `<ol>`)

```html
<ul class="dw-list"
    data-dw-num-id="1"
    data-dw-num-fmt="bullet">

<ol class="dw-list"
    data-dw-num-id="2"
    data-dw-num-fmt="decimal">
```

| Attribute | Type | Description |
|---|---|---|
| `data-dw-num-id` | string | Numbering definition ID — links list paragraphs to this list |
| `data-dw-num-fmt` | string | `bullet` \| `decimal` \| `lowerLetter` \| `upperLetter` \| `lowerRoman` \| `upperRoman` |

Nested lists are represented as nested `<ul>`/`<ol>` elements inside `<li>` elements, matching the HTML spec. Each nesting level inherits the `data-dw-num-id` of its parent list.

---

## Inline images (`<img class="dw-img">`)

```html
<img class="dw-img"
     src="data:image/png;base64,iVBOR..."
     data-dw-width="72.0"
     data-dw-height="36.0"
     data-dw-content-type="image/png"
     alt="Chart 1">
```

| Attribute | Type | Description |
|---|---|---|
| `src` | data URI | Image bytes encoded as base64 (`data:<content-type>;base64,<data>`) |
| `data-dw-width` | float (pt) | Rendered width in points |
| `data-dw-height` | float (pt) | Rendered height in points |
| `data-dw-content-type` | string | MIME type (e.g. `image/png`, `image/jpeg`) |
| `alt` | string | Alt text from Word's image description |

---

## Headers and footers (`<header>` / `<footer>`)

```html
<header class="dw-header dw-header-default" data-dw-header-type="default">
  <p class="dw-p">...</p>
</header>

<footer class="dw-footer dw-footer-default" data-dw-footer-type="default">
  <p class="dw-p dw-page-only">...</p>
</footer>
```

| Attribute | Type | Description |
|---|---|---|
| `data-dw-header-type` | string | `default` \| `first` \| `even` — which slot this header occupies |
| `data-dw-footer-type` | string | `default` \| `first` \| `even` — which slot this footer occupies |

The `data-dw-title-pg` attribute on the document div signals that a different first-page header/footer is active:

```html
<div class="dw-document" data-dw-title-pg="true" ...>
```

| Attribute | Type | Description |
|---|---|---|
| `data-dw-title-pg` | `"true"` | Document uses a distinct first-page header/footer |

---

## Page number fields (`<span class="dw-field">`)

```html
<span class="dw-field" data-dw-field="PAGE">1</span>
<span class="dw-field" data-dw-field="NUMPAGES">1</span>
```

| Attribute | Type | Description |
|---|---|---|
| `data-dw-field` | string | `PAGE` \| `NUMPAGES` \| `SECTIONPAGES` |

The text content is always the static placeholder `1`. The HTML parser reads `data-dw-field` to reconstruct the `PageNumberField` model — the placeholder text is ignored.

---

## Page breaks (`<div class="dw-page-break">`)

```html
<div class="dw-page-break" data-dw-page="2"></div>
```

| Attribute | Type | Description |
|---|---|---|
| `data-dw-page` | integer | The page number that begins after this break |

Always `display:none`. Preserved for round-trip only.

---

## Footnote and endnote references (`<a class="dw-footnote-ref">`)

```html
<a class="dw-footnote-ref"
   href="#fn-1"
   data-dw-note-type="footnote"
   data-dw-note-id="1">[1]</a>
```

| Attribute | Type | Description |
|---|---|---|
| `class` | string | `dw-footnote-ref` for footnotes, `dw-endnote-ref` for endnotes |
| `href` | string | Anchor link to the note body (`#fn-N` for footnotes, `#en-N` for endnotes) |
| `data-dw-note-type` | string | `footnote` \| `endnote` |
| `data-dw-note-id` | integer (as string) | The note ID (matches the body section entry) |

---

## Footnote and endnote sections (`<section>`)

```html
<section class="dw-footnotes" data-dw-note-section="footnotes">
  <div class="dw-fn" id="fn-1" data-dw-note-id="1" data-dw-note-type="footnote">
    <span class="dw-fn-marker">[1]</span>
    <div class="dw-fn-body">
      <p class="dw-p">Footnote content.</p>
    </div>
  </div>
</section>

<section class="dw-endnotes" data-dw-note-section="endnotes">
  <div class="dw-en" id="en-1" data-dw-note-id="1" data-dw-note-type="endnote">
    <span class="dw-en-marker">[1]</span>
    <div class="dw-fn-body">
      <p class="dw-p">Endnote content.</p>
    </div>
  </div>
</section>
```

| Element / Attribute | Description |
|---|---|
| `<section class="dw-footnotes">` | Container for all footnote bodies |
| `<section class="dw-endnotes">` | Container for all endnote bodies |
| `data-dw-note-section` | `footnotes` \| `endnotes` |
| `<div class="dw-fn">` / `<div class="dw-en">` | Individual note body container |
| `id` | `fn-N` (footnotes) or `en-N` (endnotes) — anchored from body references |
| `data-dw-note-id` | Integer note ID as string |
| `data-dw-note-type` | `footnote` \| `endnote` |
| `<span class="dw-fn-marker">` / `<span class="dw-en-marker">` | Visual marker (e.g. `[1]`) |
| `<div class="dw-fn-body">` | Container for note paragraph content |

---

## Attribute presence rules

- **Omitted = default.** Attributes are only written when their value differs from the Word default (e.g. `data-dw-align` is omitted for left-aligned paragraphs).
- **Boolean flags** (`data-dw-bold`, `data-dw-page-break-before`, etc.) are present only when `true`.
- **Numeric values** use the Python `repr` of a `float` (e.g. `"36.0"`, `"595.28"`).
