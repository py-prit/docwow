# CSS Classes

docwow generates two categories of CSS rules inside the `<style>` block of every HTML output:

1. **Base styles** — fixed rules for all docwow documents
2. **Style classes** — one rule per named Word style found in the document

---

## Base styles

These classes are always present regardless of the document content.

### `.dw-document`

The page container. `max-width` is set from the document's page width; `padding` from the four margins. Both are expressed in points (`pt`).

```css
.dw-document {
  margin: 0 auto;
  background: #ffffff;
  color: #000000;
  font-family: Calibri, 'Segoe UI', Arial, sans-serif;
  font-size: 11pt;
  line-height: 1.15;
  word-wrap: break-word;
  max-width: 595.28pt;       /* from page_width_pt */
  padding: 72pt 72pt 72pt 72pt;  /* from margins */
}
```

### `.dw-p`

Paragraph block. Margin and padding default to zero; per-paragraph spacing comes from the style class or inline style.

```css
.dw-p {
  margin: 0;
  padding: 0;
  min-height: 1em;
}
```

### `.dw-r`

Inline run. `white-space: pre-wrap` preserves the spaces and newlines that Word encodes inside runs.

```css
.dw-r {
  white-space: pre-wrap;
}
```

### `.dw-table`, `.dw-tr`, `.dw-td`

```css
.dw-table {
  border-collapse: collapse;
  margin: 6pt 0;
}
.dw-td {
  border: 1px solid #000000;
  vertical-align: top;
  padding: 4pt;
}
```

### `.dw-list`, `.dw-li`

```css
.dw-list {
  margin: 0;
  padding-left: 2em;   /* leaves room for the bullet/number marker */
}
.dw-li {
  margin: 0;
  padding-left: 0.25em;
}
```

### `.dw-img`

```css
.dw-img {
  display: inline-block;
  max-width: 100%;
}
```

### `.dw-header`, `.dw-footer`

Header and footer containers. Visual styles (border lines, smaller font, gray colour) are applied by default. The `max-width` mirrors the document page width.

```css
.dw-header, .dw-footer {
  max-width: var(--dw-page-width, 595.28pt);
  margin: 0 auto;
  padding: 4pt 72pt;
  font-size: 9pt;
  color: #555555;
  border-bottom: 1px solid #cccccc;
}
.dw-footer {
  border-top: 1px solid #cccccc;
  border-bottom: none;
}
```

### `.dw-page-break`

Always hidden. Present in the DOM only for round-trip fidelity.

```css
.dw-page-break {
  display: none;
}
```

### `.dw-page-only`

Applied to header/footer paragraphs that consist entirely of page number fields and connector words (e.g. "Page N of M"). Hidden visually but kept in the DOM so the `data-dw-field` spans survive an HTML → DOCX round-trip.

```css
.dw-page-only {
  display: none;
}
```

### `.dw-field`

Inline span for a page number field. Rendered as gray italic to signal it is a placeholder, not real content.

```css
.dw-field {
  color: #888888;
  font-style: italic;
}
```

---

## Style classes (`.dw-style-*`)

For every named Word **paragraph** style in the document, docwow emits a CSS rule:

```css
.dw-style-Heading1 {
  font-weight: bold;
  font-size: 18pt;
}
.dw-style-Heading2 {
  font-weight: bold;
  font-size: 14pt;
}
```

The class name is `.dw-style-` followed by the style's `styleId` with spaces replaced by hyphens. For example:

| Word style ID | CSS class |
|---|---|
| `Normal` | `.dw-style-Normal` |
| `Heading1` | `.dw-style-Heading1` |
| `List Paragraph` | `.dw-style-List-Paragraph` |

Each paragraph element carries both `.dw-p` and its style class:

```html
<p class="dw-p dw-style-Heading1" data-dw-style="Heading1">...</p>
```

## Character style classes (`.dw-cstyle-*`)

When a run has a named Word **character** style applied (e.g. `Strong`, `Emphasis`), it gains an additional CSS class alongside `.dw-r`:

```html
<span class="dw-r dw-cstyle-Strong" data-dw-char-style="Strong">Strong text</span>
<span class="dw-r dw-cstyle-Emphasis" data-dw-char-style="Emphasis">Italic text</span>
```

The class name is `.dw-cstyle-` followed by the character style ID with spaces replaced by hyphens:

| Word character style ID | CSS class |
|---|---|
| `Strong` | `.dw-cstyle-Strong` |
| `Emphasis` | `.dw-cstyle-Emphasis` |
| `Intense Quote` | `.dw-cstyle-Intense-Quote` |

The visual formatting of the character style (bold, italic, color, etc.) is carried directly on the span via inline `style` attributes — the `dw-cstyle-*` class is a semantic hook for custom CSS overrides. The `data-dw-char-style` attribute carries the style ID for lossless round-trip back to DOCX.

### What gets emitted into a style class

| Paragraph formatting | CSS property |
|---|---|
| `alignment` | `text-align` |
| `indent_left_pt` | `padding-left` |
| `indent_right_pt` | `padding-right` |
| `indent_first_line_pt` (positive) | `text-indent` |
| `space_before_pt` | `margin-top` |
| `space_after_pt` | `margin-bottom` |
| `line_spacing_pt` | `line-height` |

| Run formatting | CSS property |
|---|---|
| `bold` | `font-weight: bold` |
| `italic` | `font-style: italic` |
| `underline` | `text-decoration: underline` |
| `strike` | `text-decoration: line-through` |
| `small_caps` | `font-variant: small-caps` |
| `all_caps` | `text-transform: uppercase` |
| `font_name` | `font-family` |
| `font_size_pt` | `font-size` |
| `color` | `color` |

---

## Customising the visual output

Because visual appearance is entirely controlled by CSS, you can override any docwow style by injecting your own stylesheet after the docwow `<style>` block:

```html
<!-- docwow output -->
<style>/* docwow base + style classes */</style>

<!-- your overrides -->
<style>
  .dw-document { font-family: Georgia, serif; }
  .dw-style-Heading1 { color: #1a5276; }
</style>
```

This does not affect round-trip fidelity — the `data-dw-*` attributes carry all the Word metadata independently of the CSS.

---

## Bookmarks (`.dw-bookmark`)

```css
.dw-bookmark {
  display: inline;
}
```

Zero-width anchor. Marks the position of a `w:bookmarkStart` element in the document body. Renders as an empty `<a id="name">` element. Invisible in the browser; used as a fragment target for `#name` hyperlinks.

---

## Footnotes and endnotes

### `.dw-footnote-ref`, `.dw-endnote-ref`

Inline superscript reference markers (e.g. `[1]`) that link to the note body section at the bottom of the page.

```css
.dw-footnote-ref, .dw-endnote-ref {
  color: #1565C0;
  font-size: 0.75em;
  vertical-align: super;
  line-height: 1;
  text-decoration: none;
}
.dw-footnote-ref:hover, .dw-endnote-ref:hover {
  text-decoration: underline;
}
```

### `.dw-footnotes`, `.dw-endnotes`

Note body sections at the bottom of the rendered document.

```css
.dw-footnotes, .dw-endnotes {
  margin-top: 24pt;
  padding-top: 12pt;
  border-top: 1px solid #cccccc;
  font-size: 9pt;
  color: #333333;
}
```

### `.dw-fn`, `.dw-en`

Individual footnote / endnote body containers.

```css
.dw-fn, .dw-en {
  display: flex;
  gap: 6pt;
  margin-bottom: 6pt;
}
.dw-fn-marker, .dw-en-marker {
  flex-shrink: 0;
  font-weight: bold;
  color: #1565C0;
  min-width: 2em;
}
.dw-fn-body, .dw-en-body {
  flex: 1;
}
```

---

## Table of Contents (`.dw-toc`)

```css
.dw-toc {
  margin: 12pt 0;
  padding: 10pt 14pt;
  background: #f8f8f8;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}
.dw-toc-title {
  font-weight: bold;
  font-size: 11pt;
  margin-bottom: 8pt;
}
.dw-toc-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.dw-toc-entry {
  margin: 3pt 0;
}
.dw-toc-level-1 { padding-left: 0; }
.dw-toc-level-2 { padding-left: 16pt; }
.dw-toc-level-3 { padding-left: 32pt; }
/* ... up to level-9 */
.dw-toc-link {
  color: #1a1a1a;
  text-decoration: none;
}
.dw-toc-link:hover {
  text-decoration: underline;
}
```

---

## Comments

### `.dw-comment-ref`

Inline superscript reference marker (e.g. `[1]`). Styled in orange to match Word's comment colour. Uses CSS `:hover` to show the popup — no JavaScript.

```css
.dw-comment-ref {
  position: relative;
  color: #E65100;
  font-size: 0.75em;
  vertical-align: super;
  line-height: 1;
  text-decoration: none;
  cursor: pointer;
}
```

### `.dw-comment-popup`

CSS hover popup shown when hovering over a comment reference.

```css
.dw-comment-popup {
  display: none;
  position: absolute;
  /* ... positioned above the ref marker */
}
.dw-comment-ref:hover .dw-comment-popup {
  display: block;
}
```

### `.dw-comments`

Hidden section at the bottom of the document containing full comment metadata for HTML→DOCX round-trip. Always `display: none`.

```css
.dw-comments {
  display: none;
}
```

---

## Track changes

### `ins.dw-ins`

Inserted text. Green underline with a subtle green background.

```css
ins.dw-ins {
  position: relative;
  color: #1B5E20;
  text-decoration: underline;
  text-decoration-color: #1B5E20;
  background-color: rgba(46, 125, 50, 0.08);
  cursor: pointer;
}
```

### `del.dw-del`

Deleted text. Red strikethrough with a subtle red background.

```css
del.dw-del {
  position: relative;
  color: #B71C1C;
  text-decoration: line-through;
  text-decoration-color: #B71C1C;
  background-color: rgba(183, 28, 28, 0.08);
  cursor: pointer;
}
```

### `.dw-tc-popup`

Hover popup containing author, date, and Accept/Reject buttons. Shown via CSS `:hover` on the parent `ins`/`del` element. The popup is purely visual — it is ignored by the HTML parser on round-trip.

```css
.dw-tc-popup {
  display: none;
  position: absolute;
  /* ... positioned above the changed text */
}
ins.dw-ins:hover .dw-tc-popup,
del.dw-del:hover .dw-tc-popup {
  display: block;
}
```

Accept/Reject buttons (`.dw-tc-accept`, `.dw-tc-reject`) are styled inline. Clicking them triggers the `dwTcAccept()` / `dwTcReject()` JavaScript functions injected into the `<script>` block at the end of `<body>`.
