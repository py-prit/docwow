"""Parse <table class="dw-table"> elements into Table model objects."""
from __future__ import annotations

from docwow.html_parser._utils import has_class, pt_val
from docwow.html_parser.paragraph_parser import parse_paragraph
from docwow.models.table import Table, TableCell, TableRow


def parse_table(table_el) -> Table:
    """Parse a <table class="dw-table"> lxml element into a Table."""
    col_widths_str = table_el.get("data-dw-col-widths", "")
    col_widths_pt = tuple(
        pt_val(w.strip()) or 0.0
        for w in col_widths_str.split(",")
        if w.strip()
    )
    return Table(
        rows=tuple(_parse_row(tr) for tr in table_el if tr.tag == "tr"),
        style_id=table_el.get("data-dw-style"),
        width_pt=pt_val(table_el.get("data-dw-width")),
        col_widths_pt=col_widths_pt,
    )


def _parse_row(tr_el) -> TableRow:
    return TableRow(
        cells=tuple(_parse_cell(td) for td in tr_el if td.tag == "td"),
        height_pt=pt_val(tr_el.get("data-dw-height")),
    )


def _parse_cell(td_el) -> TableCell:
    paragraphs = tuple(
        parse_paragraph(child)
        for child in td_el
        if child.tag == "p" and has_class(child, "dw-p")
    )
    return TableCell(
        paragraphs=paragraphs,
        col_span=int(td_el.get("colspan", "1")),
        row_span=int(td_el.get("rowspan", "1")),
        width_pt=pt_val(td_el.get("data-dw-width")),
        v_merge_start=td_el.get("data-dw-v-merge-start") == "true",
        v_merge_continue=td_el.get("data-dw-v-merge-continue") == "true",
        shading=td_el.get("data-dw-shading") or None,
    )
