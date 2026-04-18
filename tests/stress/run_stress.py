"""
Stress test docwow against real-world DOCX files.

For each file in tests/stress/docx/:
  1. Parse DOCX → mutable document (open)
  2. Render to HTML (to_html)
  3. Convert HTML back to DOCX (to_docx)
  4. Re-parse the round-tripped DOCX
  5. Semantic diff: compare every supported feature between original and round-trip

Checks: body structure, paragraphs, runs (all types), formatting (bold/italic/
underline/strike/color/font/size/vanish/caps/vertical-align), list info, para
formatting (style/alignment/indents/spacing/borders/tabs/shading/page-break/
keep-together), tables (rows/cells/cell content), images (inline + floating,
size + data), hyperlinks (URL + runs), footnote refs, bookmarks, cross-refs,
comment refs, tracked changes, page number fields.

Run from the project root:
    source venv/bin/activate
    python tests/stress/run_stress.py
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import docwow
from docwow.api.comment import MutableCommentRef
from docwow.api.footnote import MutableFootnoteRef
from docwow.api.paragraph import MutableParagraph, MutableSectionBreak
from docwow.api.run import (
    MutableBookmark,
    MutableCrossRef,
    MutableFloatingImageRun,
    MutableHyperlink,
    MutableImageRun,
    MutablePageNumberField,
    MutableRun,
    MutableTrackedChange,
)
from docwow.api.table import MutableTable
from docwow.models.paragraph import PageBreak

DOCX_DIR = Path(__file__).parent / "docx"
PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
WARN = "\033[33m⚠\033[0m"


# ---------------------------------------------------------------------------
# Fingerprinting — produce a comparable representation of a document
# ---------------------------------------------------------------------------

def _fp_run(run: Any) -> dict:
    if isinstance(run, MutableRun):
        return {
            "T": "text",
            "text": run.get_text(),
            "bold": run.bold,
            "italic": run.italic,
            "underline": run.underline,
            "strike": run.strike,
            "small_caps": run.small_caps,
            "all_caps": run.all_caps,
            "vanish": run.vanish,
            "font_name": run.font_name,
            "font_size": run.font_size,
            "color": (run.color or "").upper() if run.color else None,
            "highlight": run.highlight,
            "vertical_align": run.vertical_align,
            "char_style_id": run.char_style_id,
        }
    if isinstance(run, MutableImageRun):
        img = run.get_image()
        return {
            "T": "image",
            "width_pt": round(run.width_pt, 0),
            "height_pt": round(run.height_pt, 0),
            "content_type": run.content_type,
            "data_len": len(img.data),
        }
    if isinstance(run, MutableFloatingImageRun):
        img = run.get_image()
        return {
            "T": "float_image",
            "width_pt": round(run.width_pt, 0),
            "height_pt": round(run.height_pt, 0),
            "content_type": run.content_type,
            "data_len": len(img.data),
            "wrap": run.wrap,
            "pos_h_pt": round(run.pos_h_pt, 0),
            "pos_v_pt": round(run.pos_v_pt, 0),
            "behind_doc": run.behind_doc,
        }
    if isinstance(run, MutableHyperlink):
        return {
            "T": "hyperlink",
            "url": run.url,
            "text": run.get_text(),
        }
    if isinstance(run, MutablePageNumberField):
        return {"T": "page_field", "field_type": run.field_type}
    if isinstance(run, MutableFootnoteRef):
        return {"T": "footnote_ref", "note_id": run.note_id, "note_type": run.note_type}
    if isinstance(run, MutableBookmark):
        return {"T": "bookmark", "name": run.name}
    if isinstance(run, MutableCrossRef):
        return {"T": "xref", "bookmark_name": run.bookmark_name, "display_text": run.display_text}
    if isinstance(run, MutableCommentRef):
        return {"T": "comment_ref", "comment_id": run.comment_id}
    if isinstance(run, MutableTrackedChange):
        return {
            "T": "tracked_change",
            "change_type": run.change_type,
            "author": run.author,
            "text": run.get_text(),
        }
    return {"T": type(run).__name__}


def _fp_para_fmt(p: MutableParagraph) -> dict:
    return {
        "style_id": p.style_id,
        "alignment": p.alignment,
        "indent_left_pt": round(p.indent_left_pt or 0, 1),
        "indent_right_pt": round(p.indent_right_pt or 0, 1),
        "indent_first_line_pt": round(p.indent_first_line_pt or 0, 1),
        "space_before_pt": round(p.space_before_pt or 0, 1),
        "space_after_pt": round(p.space_after_pt or 0, 1),
        "line_spacing_pt": round(p.line_spacing_pt, 1) if p.line_spacing_pt else None,
        "keep_together": p.keep_together,
        "keep_with_next": p.keep_with_next,
        "page_break_before": p.page_break_before,
        "shading": p.shading,
        "tab_stops": [(round(t.position_pt, 1), t.alignment, t.leader) for t in (p.tab_stops or ())],
        "borders": _fp_borders(p.borders),
    }


def _fp_borders(b: Any) -> dict | None:
    if b is None:
        return None
    result = {}
    for side in ("top", "left", "bottom", "right"):
        bd = getattr(b, side, None)
        if bd:
            result[side] = {"style": bd.style, "width_pt": round(bd.width_pt, 2), "color": bd.color}
    return result or None


def _fp_paragraph(p: MutableParagraph) -> dict:
    li = p.list_info
    return {
        "T": "para",
        "fmt": _fp_para_fmt(p),
        "list_info": {"num_id": li.num_id, "level": li.level} if li else None,
        "runs": [_fp_run(r) for r in p.runs],
    }


def _fp_cell(cell: Any) -> dict:
    paras = []
    for item in cell.paragraphs:
        if isinstance(item, MutableParagraph):
            paras.append(_fp_paragraph(item))
    return {"paras": paras}


def _fp_table(t: MutableTable) -> dict:
    return {
        "T": "table",
        "rows": [
            {"cells": [_fp_cell(cell) for cell in row]}
            for row in t
        ],
    }


def _fp_body_element(item: Any) -> dict:
    if isinstance(item, MutableParagraph):
        return _fp_paragraph(item)
    if isinstance(item, MutableTable):
        return _fp_table(item)
    if isinstance(item, PageBreak):
        return {"T": "page_break"}
    if isinstance(item, MutableSectionBreak):
        return {"T": "section_break"}
    return {"T": type(item).__name__}


def _fingerprint(doc: Any) -> list[dict]:
    return [_fp_body_element(item) for item in doc.paragraphs]


# ---------------------------------------------------------------------------
# Diffing — compare two fingerprints and collect human-readable diffs
# ---------------------------------------------------------------------------

def _diff_value(path: str, a: Any, b: Any, diffs: list[str]) -> None:
    if a != b:
        diffs.append(f"{path}: {a!r} → {b!r}")


def _diff_run(path: str, a: dict, b: dict, diffs: list[str]) -> None:
    if a.get("T") != b.get("T"):
        diffs.append(f"{path}: run type {a.get('T')!r} → {b.get('T')!r}")
        return
    t = a["T"]
    skip = {"T"}
    if t == "text":
        skip |= {"char_style_id"}  # style IDs may be remapped
    if t in ("image", "float_image"):
        skip |= {"data_len"}  # re-encoded images may differ in byte count
    for k in set(a) | set(b):
        if k in skip:
            continue
        _diff_value(f"{path}.{k}", a.get(k), b.get(k), diffs)


def _diff_runs(path: str, a: list, b: list, diffs: list[str]) -> None:
    if len(a) != len(b):
        diffs.append(f"{path}: run count {len(a)} → {len(b)}")
        # still compare up to min length
    for i, (ra, rb) in enumerate(zip(a, b)):
        _diff_run(f"{path}[{i}]", ra, rb, diffs)


def _diff_para(path: str, a: dict, b: dict, diffs: list[str]) -> None:
    _diff_value(f"{path}.list_info", a.get("list_info"), b.get("list_info"), diffs)

    fa, fb = a.get("fmt", {}), b.get("fmt", {})
    skip_fmt = {"style_id"}  # style IDs may differ after round-trip
    for k in set(fa) | set(fb):
        if k in skip_fmt:
            continue
        _diff_value(f"{path}.fmt.{k}", fa.get(k), fb.get(k), diffs)

    _diff_runs(f"{path}.runs", a.get("runs", []), b.get("runs", []), diffs)


def _diff_cell(path: str, a: dict, b: dict, diffs: list[str]) -> None:
    paras_a, paras_b = a.get("paras", []), b.get("paras", [])
    if len(paras_a) != len(paras_b):
        diffs.append(f"{path}: cell para count {len(paras_a)} → {len(paras_b)}")
    for i, (pa, pb) in enumerate(zip(paras_a, paras_b)):
        _diff_para(f"{path}.p[{i}]", pa, pb, diffs)


def _diff_table(path: str, a: dict, b: dict, diffs: list[str]) -> None:
    rows_a, rows_b = a.get("rows", []), b.get("rows", [])
    if len(rows_a) != len(rows_b):
        diffs.append(f"{path}: row count {len(rows_a)} → {len(rows_b)}")
    for ri, (ra, rb) in enumerate(zip(rows_a, rows_b)):
        cells_a, cells_b = ra.get("cells", []), rb.get("cells", [])
        if len(cells_a) != len(cells_b):
            diffs.append(f"{path}.row[{ri}]: cell count {len(cells_a)} → {len(cells_b)}")
        for ci, (ca, cb) in enumerate(zip(cells_a, cells_b)):
            _diff_cell(f"{path}.row[{ri}].cell[{ci}]", ca, cb, diffs)


def _diff_element(path: str, a: dict, b: dict, diffs: list[str]) -> None:
    ta, tb = a.get("T"), b.get("T")
    if ta != tb:
        diffs.append(f"{path}: element type {ta!r} → {tb!r}")
        return
    if ta == "para":
        _diff_para(path, a, b, diffs)
    elif ta == "table":
        _diff_table(path, a, b, diffs)
    # page_break and section_break have no sub-fields to diff


def _diff_fingerprints(fp1: list[dict], fp2: list[dict]) -> list[str]:
    diffs: list[str] = []
    if len(fp1) != len(fp2):
        diffs.append(f"body element count: {len(fp1)} → {len(fp2)}")
    for i, (a, b) in enumerate(zip(fp1, fp2)):
        _diff_element(f"body[{i}]", a, b, diffs)
    return diffs


# ---------------------------------------------------------------------------
# Per-file runner
# ---------------------------------------------------------------------------

def run_file(path: Path) -> dict:
    result: dict[str, Any] = {
        "file": path.name,
        "status": "ok",
        "stage": None,
        "error": None,
        "diffs": [],
        "elapsed_ms": 0,
    }

    t0 = time.perf_counter()

    try:
        result["stage"] = "open"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc1 = docwow.open(path.read_bytes())
        fp1 = _fingerprint(doc1)

        result["stage"] = "to_html"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = docwow.to_html(path.read_bytes())

        result["stage"] = "to_docx"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            docx_bytes = docwow.to_docx(html)

        result["stage"] = "reopen"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc2 = docwow.open(docx_bytes)
        fp2 = _fingerprint(doc2)

        result["stage"] = "diff"
        diffs = _diff_fingerprints(fp1, fp2)
        result["diffs"] = diffs
        result["stage"] = None
        result["status"] = "ok" if not diffs else "partial"

    except Exception as e:
        result["status"] = "crash"
        result["error"] = f"{type(e).__name__}: {e}"

    result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    files = sorted(DOCX_DIR.glob("*.docx"))
    if not files:
        print(f"No .docx files found in {DOCX_DIR}")
        sys.exit(1)

    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    print(f"\ndocwow stress test — {len(files)} files\n{'─' * 72}")

    results = []
    for path in files:
        r = run_file(path)
        results.append(r)

        if r["status"] == "crash":
            icon = FAIL
            detail = f"  → crashed at [{r['stage']}]: {r['error']}"
        elif r["status"] == "partial":
            icon = WARN
            detail = f"  → {len(r['diffs'])} diff(s)  {r['elapsed_ms']}ms"
        else:
            icon = PASS
            detail = f"  {r['elapsed_ms']}ms"

        print(f"{icon}  {r['file']:<50}{detail}")

        if verbose and r["diffs"]:
            for d in r["diffs"][:10]:
                print(f"       {d}")
            if len(r["diffs"]) > 10:
                print(f"       … and {len(r['diffs']) - 10} more")

    total   = len(results)
    ok      = sum(1 for r in results if r["status"] == "ok")
    partial = sum(1 for r in results if r["status"] == "partial")
    crash   = sum(1 for r in results if r["status"] == "crash")

    print(f"\n{'─' * 72}")
    print(f"Total: {total}   {PASS} OK: {ok}   {WARN} Partial: {partial}   {FAIL} Crash: {crash}")

    if crash > 0:
        print(f"\nCrashes:")
        for r in results:
            if r["status"] == "crash":
                print(f"  {r['file']}: [{r['stage']}] {r['error']}")

    if partial > 0:
        print(f"\nSemantic diffs (run with -v for detail):")
        for r in results:
            if r["status"] == "partial":
                print(f"  {r['file']} — {len(r['diffs'])} diff(s):")
                for d in r["diffs"][:5]:
                    print(f"    {d}")
                if len(r["diffs"]) > 5:
                    print(f"    … and {len(r['diffs']) - 5} more")

    print()
    sys.exit(0 if crash == 0 else 1)


if __name__ == "__main__":
    main()
