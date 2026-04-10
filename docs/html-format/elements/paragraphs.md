# Paragraphs

Every Word paragraph is rendered as a `<p class="dw-p">` element.

## Basic paragraph

```html
<p class="dw-p dw-style-Normal" data-dw-style="Normal">
  <span class="dw-r">This is a paragraph.</span>
</p>
```

## Paragraph with formatting

```html
<p class="dw-p dw-style-Normal"
   data-dw-style="Normal"
   data-dw-align="justify"
   data-dw-indent-left="36.0"
   data-dw-space-before="12.0"
   data-dw-space-after="6.0">
  <span class="dw-r">Indented, justified paragraph with spacing.</span>
</p>
```

The CSS classes handle visual rendering; the `data-dw-*` attributes carry the original point values for round-trip reconstruction.

## Run formatting

Each inline formatting run is a `<span class="dw-r">`:

```html
<p class="dw-p dw-style-Normal" data-dw-style="Normal">
  <span class="dw-r" data-dw-bold="true" style="font-weight:bold">Bold</span>
  <span class="dw-r"> normal </span>
  <span class="dw-r" data-dw-italic="true" data-dw-color="FF0000"
        style="font-style:italic;color:#FF0000">red italic</span>
</p>
```

## Newlines within a run

Word allows newlines within a single run (`<w:br/>`). These are preserved as literal `\n` characters in the span's text content and rendered correctly via `white-space: pre-wrap`.

```html
<span class="dw-r">Line 1
Line 2
Line 3</span>
```

## Headings

Heading paragraphs use the named style class for their visual appearance:

```html
<p class="dw-p dw-style-Heading1" data-dw-style="Heading1">
  <span class="dw-r">Section Title</span>
</p>
```

The `.dw-style-Heading1` CSS class carries the font size and weight defined in the document's styles.

## Page breaks

A paragraph with a page-break-before flag:

```html
<p class="dw-p dw-style-Normal"
   data-dw-style="Normal"
   data-dw-page-break-before="true"
   style="page-break-before:always">
  <span class="dw-r">Starts on a new page.</span>
</p>
```
