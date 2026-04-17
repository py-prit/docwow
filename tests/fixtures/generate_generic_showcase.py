"""
Generate generic_showcase.docx from generic_input.html.

This script demonstrates the general HTML→DOCX conversion path
(is_foreign_html=True).  Run after any Phase 2 sub-feature lands to
regenerate the showcase and verify the output in Word / LibreOffice.

    python tests/fixtures/generate_generic_showcase.py

Expand generic_input.html as new sub-features ship:
  feat/generic-inline-elements → add formatted inline content
  feat/generic-lists            → add <ul>/<ol> examples
  feat/generic-tables           → add <table> examples
  feat/generic-images           → add <img> examples
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import docwow

FIXTURES = Path(__file__).parent
INPUT_HTML = FIXTURES / "generic_input.html"
OUTPUT_DOCX = FIXTURES / "generic_showcase.docx"

html = INPUT_HTML.read_text(encoding="utf-8")
docwow.to_docx(html, target=OUTPUT_DOCX, is_foreign_html=True)
print(f"Written: {OUTPUT_DOCX}  ({OUTPUT_DOCX.stat().st_size:,} bytes)")
