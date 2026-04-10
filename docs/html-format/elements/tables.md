# Tables

Word tables are rendered as standard HTML `<table>` elements with docwow CSS classes and `data-dw-*` attributes carrying the Word-specific metadata.

## Basic table

```html
<table class="dw-table"
       data-dw-width="360.0"
       data-dw-col-widths="120.0,120.0,120.0">
  <tr class="dw-tr">
    <td class="dw-td" data-dw-width="120.0">
      <p class="dw-p dw-style-Normal" data-dw-style="Normal">
        <span class="dw-r">Cell 1</span>
      </p>
    </td>
    <td class="dw-td" data-dw-width="120.0">
      <p class="dw-p dw-style-Normal" data-dw-style="Normal">
        <span class="dw-r">Cell 2</span>
      </p>
    </td>
    <td class="dw-td" data-dw-width="120.0">
      <p class="dw-p dw-style-Normal" data-dw-style="Normal">
        <span class="dw-r">Cell 3</span>
      </p>
    </td>
  </tr>
</table>
```

## Column span (merged columns)

```html
<td class="dw-td" colspan="2" data-dw-width="240.0">
  <p class="dw-p dw-style-Normal" data-dw-style="Normal">
    <span class="dw-r">Spans two columns</span>
  </p>
</td>
```

The HTML `colspan` attribute handles visual rendering. `data-dw-width` records the combined column width in points.

## Row span (merged rows)

Word's vertical cell merge uses a different mechanism from HTML `rowspan`. docwow uses both representations simultaneously:

- The HTML `rowspan` attribute on the first cell controls visual rendering
- `data-dw-v-merge-start="true"` marks the first cell of a vertical merge group
- `data-dw-v-merge-continue="true"` marks continuation cells (which still appear in the HTML but are hidden by `rowspan`)

```html
<!-- Row 1: merge starts here -->
<tr class="dw-tr">
  <td class="dw-td" rowspan="2" data-dw-v-merge-start="true">
    <p class="dw-p dw-style-Normal" data-dw-style="Normal">
      <span class="dw-r">Spans two rows</span>
    </p>
  </td>
  <td class="dw-td"><p class="dw-p dw-style-Normal" data-dw-style="Normal"><span class="dw-r">Row 1 Col 2</span></p></td>
</tr>

<!-- Row 2: continuation cell (hidden by rowspan, but preserved for round-trip) -->
<tr class="dw-tr">
  <td class="dw-td" data-dw-v-merge-continue="true" style="display:none"></td>
  <td class="dw-td"><p class="dw-p dw-style-Normal" data-dw-style="Normal"><span class="dw-r">Row 2 Col 2</span></p></td>
</tr>
```

!!! warning "Preserve continuation cells"
    When building a browser editor, do not remove `data-dw-v-merge-continue` cells from the DOM. They must be present for the HTML parser to reconstruct the correct `<w:vMerge>` structure in DOCX.
