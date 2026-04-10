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

---

## Style classes (`.dw-style-*`)

For every named Word style in the document, docwow emits a CSS rule:

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
