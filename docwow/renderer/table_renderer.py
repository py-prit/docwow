"""Render Table objects to HTML <table> elements."""

from __future__ import annotations

from docwow.models.table import Table, TableCell, TableRow
from docwow.renderer.paragraph_renderer import render_paragraph
from docwow.utils.units import pt_to_css


def render_table(table: Table) -> str:
    """Return a <table> HTML element."""
    attrs: list[str] = ['class="dw-table"']

    style_parts: list[str] = ["border-collapse:collapse"]
    if table.width_pt is not None:
        style_parts.append(f"width:{pt_to_css(table.width_pt)}")
        attrs.append(f'data-dw-width="{pt_to_css(table.width_pt)}"')

    if table.style_id:
        attrs.append(f'data-dw-style="{table.style_id}"')

    if table.col_widths_pt:
        widths_str = ",".join(pt_to_css(w) for w in table.col_widths_pt)
        attrs.append(f'data-dw-col-widths="{widths_str}"')

    attrs.append(f'style="{";".join(style_parts)}"')

    rows_html = "\n".join(_render_row(row) for row in table.rows)
    attrs_str = " ".join(attrs)
    return f"<table {attrs_str}>\n{rows_html}\n</table>"


def _render_row(row: TableRow) -> str:
    attrs: list[str] = ['class="dw-tr"']
    style_parts: list[str] = []

    if row.height_pt is not None:
        style_parts.append(f"height:{pt_to_css(row.height_pt)}")
        attrs.append(f'data-dw-height="{pt_to_css(row.height_pt)}"')

    if style_parts:
        attrs.append(f'style="{";".join(style_parts)}"')

    cells_html = "\n".join(_render_cell(cell) for cell in row.cells)
    attrs_str = " ".join(attrs)
    return f"<tr {attrs_str}>\n{cells_html}\n</tr>"


def _render_cell(cell: TableCell) -> str:
    attrs: list[str] = ['class="dw-td"']
    style_parts: list[str] = ["vertical-align:top", "padding:4pt"]

    if cell.width_pt is not None:
        style_parts.append(f"width:{pt_to_css(cell.width_pt)}")
        attrs.append(f'data-dw-width="{pt_to_css(cell.width_pt)}"')

    if cell.col_span > 1:
        attrs.append(f'colspan="{cell.col_span}"')
        attrs.append(f'data-dw-col-span="{cell.col_span}"')

    if cell.row_span > 1:
        attrs.append(f'rowspan="{cell.row_span}"')
        attrs.append(f'data-dw-row-span="{cell.row_span}"')

    if cell.v_merge_start:
        attrs.append('data-dw-v-merge-start="true"')
    if cell.v_merge_continue:
        attrs.append('data-dw-v-merge-continue="true"')
        # Continuation cells are visually hidden (content is in the start cell)
        style_parts.append("display:none")

    if cell.shading:
        attrs.append(f'data-dw-shading="{cell.shading}"')
        style_parts.append(f"background-color:#{cell.shading}")

    attrs.append(f'style="{";".join(style_parts)}"')

    content = "\n".join(render_paragraph(p) for p in cell.paragraphs)
    attrs_str = " ".join(attrs)
    return f"<td {attrs_str}>{content}</td>"
