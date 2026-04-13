# Hyperlinks

Hyperlinks are rendered as `<a class="dw-hyperlink">` elements containing one or more `<span class="dw-r">` run children.

## HTML representation

```html
<p class="dw-p" data-dw-style="Normal">
  <span class="dw-r">Visit the </span>
  <a href="https://docwow.readthedocs.io"
     class="dw-hyperlink"
     data-dw-href="https://docwow.readthedocs.io">
    <span class="dw-r">docwow documentation</span>
  </a>
  <span class="dw-r"> for more details.</span>
</p>
```

A mailto link looks identical, just with a different scheme:

```html
<a href="mailto:hello@example.com"
   class="dw-hyperlink"
   data-dw-href="mailto:hello@example.com">
  <span class="dw-r">hello@example.com</span>
</a>
```

## Attributes

| Attribute | Description |
|---|---|
| `href` | The URL — used by browsers for navigation |
| `data-dw-href` | The URL — used by the docwow HTML parser for round-trip reconstruction |
| `class="dw-hyperlink"` | Identifies this element as a docwow hyperlink |

The URL is HTML-escaped in both `href` and `data-dw-href` (e.g. `&` → `&amp;`).

## Inner structure

Each `<a>` contains one or more `<span class="dw-r">` runs, identical to the run format used inside paragraphs. Run formatting (bold, italic, font size, etc.) is supported on hyperlink inner runs.

## Round-trip

When the HTML parser encounters `<a data-dw-href="...">`, it reads the URL from `data-dw-href` and reconstructs the `Hyperlink` model. The `href` attribute is ignored during parsing — `data-dw-href` is the authoritative source.

Plain `<a>` elements without `data-dw-href` are ignored by the parser.
