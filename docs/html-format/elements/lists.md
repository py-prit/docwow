# Lists

Word lists are rendered as nested `<ul>` / `<ol>` elements. Each list paragraph becomes a `<li>` containing a `<p class="dw-p">`.

## Bullet list

```html
<ul class="dw-list" data-dw-num-id="1" data-dw-num-fmt="bullet">
  <li class="dw-li">
    <p class="dw-p dw-style-Normal"
       data-dw-style="Normal"
       data-dw-num-id="1"
       data-dw-level="0">
      <span class="dw-r">First item</span>
    </p>
  </li>
  <li class="dw-li">
    <p class="dw-p dw-style-Normal"
       data-dw-style="Normal"
       data-dw-num-id="1"
       data-dw-level="0">
      <span class="dw-r">Second item</span>
    </p>
  </li>
</ul>
```

## Numbered list

```html
<ol class="dw-list" data-dw-num-id="2" data-dw-num-fmt="decimal">
  <li class="dw-li">
    <p class="dw-p dw-style-Normal"
       data-dw-style="Normal"
       data-dw-num-id="2"
       data-dw-level="0">
      <span class="dw-r">First numbered item</span>
    </p>
  </li>
</ol>
```

## Nested lists

Sub-levels are represented as nested `<ul>`/`<ol>` elements inside `<li>`:

```html
<ul class="dw-list" data-dw-num-id="1" data-dw-num-fmt="bullet">
  <li class="dw-li">
    <p class="dw-p dw-style-Normal" data-dw-style="Normal"
       data-dw-num-id="1" data-dw-level="0">
      <span class="dw-r">Top-level item</span>
    </p>
    <ul class="dw-list" data-dw-num-id="1" data-dw-num-fmt="bullet">
      <li class="dw-li">
        <p class="dw-p dw-style-Normal" data-dw-style="Normal"
           data-dw-num-id="1" data-dw-level="1">
          <span class="dw-r">Nested item</span>
        </p>
      </li>
    </ul>
  </li>
</ul>
```

## `data-dw-num-id` linking

The `data-dw-num-id` on the `<ul>`/`<ol>` and on each `<p class="dw-p">` must match. This is how the HTML parser reconstructs the `NumberingDefinition` and links each paragraph to the correct list.

Multiple distinct lists in the same document each get a unique `num-id`:

```html
<ul data-dw-num-id="1" ...>...</ul>  <!-- first list -->
<ul data-dw-num-id="3" ...>...</ul>  <!-- different list, different id -->
```
