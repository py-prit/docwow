# Images

Inline images are rendered as `<img class="dw-img">` elements embedded directly inside paragraph runs. All image data is embedded as a base64 data URI — no external files.

## HTML representation

```html
<p class="dw-p dw-style-Normal" data-dw-style="Normal">
  <span class="dw-r">Before image — </span>
  <img class="dw-img"
       src="data:image/png;base64,iVBORw0KGgo..."
       data-dw-width="72.0"
       data-dw-height="36.0"
       data-dw-content-type="image/png"
       alt="Chart title"
       style="width:72.0pt;height:36.0pt">
  <span class="dw-r"> — after image</span>
</p>
```

## Attributes

| Attribute | Description |
|---|---|
| `src` | Base64 data URI containing the full image binary |
| `data-dw-width` | Original Word width in points |
| `data-dw-height` | Original Word height in points |
| `data-dw-content-type` | MIME type (e.g. `image/png`, `image/jpeg`, `image/gif`) |
| `alt` | Alt text from Word's image description field |

The inline `style` attribute sets `width` and `height` in points so the image renders at its intended size in the browser.

## Supported formats

| MIME type | Extension |
|---|---|
| `image/png` | `.png` |
| `image/jpeg` | `.jpg` |
| `image/gif` | `.gif` |
| `image/bmp` | `.bmp` |
| `image/tiff` | `.tiff` |
| `image/webp` | `.webp` |
| `image/svg+xml` | `.svg` |
| `image/x-emf` | `.emf` |
| `image/x-wmf` | `.wmf` |

## Round-trip

When converting back to DOCX, the base64 data is decoded from the `src` attribute, written to the ZIP's `word/media/` folder, and linked via a relationship. The `data-dw-content-type` attribute determines the file extension used for the media entry.
