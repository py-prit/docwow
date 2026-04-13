# Headers & Footers

Headers and footers are rendered as HTML `<header>` and `<footer>` elements placed as siblings of the `.dw-document` div, inside `<body>`.

## Document structure

```html
<body>
  <header class="dw-header dw-header-default" data-dw-header-type="default">
    ...
  </header>

  <div class="dw-document" ...>
    <!-- body paragraphs, tables, lists -->
  </div>

  <footer class="dw-footer dw-footer-default" data-dw-footer-type="default">
    ...
  </footer>
</body>
```

The `<header>` elements come before the document div; `<footer>` elements come after. Up to six elements may be present (default, first, even for each type).

## Attributes

| Attribute | Values | Description |
|---|---|---|
| `class` | `dw-header dw-header-{type}` or `dw-footer dw-footer-{type}` | Element type and slot |
| `data-dw-header-type` | `default` \| `first` \| `even` | Which slot this header occupies |
| `data-dw-footer-type` | `default` \| `first` \| `even` | Which slot this footer occupies |

## Inner structure

The content of a `<header>` or `<footer>` is a sequence of `<p class="dw-p">` paragraphs, identical in structure to body paragraphs.

```html
<header class="dw-header dw-header-default" data-dw-header-type="default">
  <p class="dw-p">
    <span class="dw-r" data-dw-italic="true" style="font-style:italic">
      My Company — Quarterly Report
    </span>
  </p>
</header>
```

## Page number fields

Page number fields inside paragraphs are rendered as `<span class="dw-field">`:

```html
<footer class="dw-footer dw-footer-default" data-dw-footer-type="default">
  <p class="dw-p">
    <span class="dw-r">Page </span>
    <span class="dw-field" data-dw-field="PAGE">1</span>
    <span class="dw-r"> of </span>
    <span class="dw-field" data-dw-field="NUMPAGES">1</span>
  </p>
</footer>
```

The text content (`1`) is a static placeholder. The actual page number is not computed in HTML — see [known limitations](../../user-guide/headers-footers.md#known-limitations).

| Attribute | Values | Description |
|---|---|---|
| `class` | `dw-field` | Identifies this as a page number field |
| `data-dw-field` | `PAGE` \| `NUMPAGES` \| `SECTIONPAGES` | The Word field type |

## Hidden page-number-only paragraphs

Paragraphs that consist entirely of page number fields and connector words (e.g. "Page N of M") are given the `dw-page-only` CSS class, which hides them visually:

```html
<footer class="dw-footer dw-footer-default" data-dw-footer-type="default">
  <p class="dw-p dw-page-only">
    <span class="dw-r">Page </span>
    <span class="dw-field" data-dw-field="PAGE">1</span>
    <span class="dw-r"> of </span>
    <span class="dw-field" data-dw-field="NUMPAGES">1</span>
  </p>
</footer>
```

The paragraph is `display:none` in the browser but its `data-dw-field` spans are preserved in the DOM so an HTML → DOCX conversion can recover the page number fields.

## Page breaks

Explicit page breaks in the document body are rendered as hidden `<div>` elements:

```html
<div class="dw-page-break" data-dw-page="2"></div>
```

| Attribute | Type | Description |
|---|---|---|
| `class` | `dw-page-break` | Always `display:none` |
| `data-dw-page` | integer | The page number that starts after this break |

Page break divs are always invisible in the browser. They exist solely for round-trip fidelity — the HTML parser emits a `PageBreak` model element when it encounters one, which the DOCX writer converts back to `<w:br w:type="page"/>`.

## Round-trip

The HTML parser reconstructs headers and footers by scanning `<header>` and `<footer>` siblings of the `.dw-document` div. It reads:

- `data-dw-header-type` / `data-dw-footer-type` to determine the slot
- `<p class="dw-p">` children as paragraphs (same parser as body paragraphs)
- `<span class="dw-field" data-dw-field="...">` as `PageNumberField` runs
- `<div class="dw-page-break">` in the body as `PageBreak` elements

Elements without `data-dw-header-type` / `data-dw-footer-type` attributes are ignored.
