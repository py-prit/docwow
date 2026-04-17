# Planned Improvements

Technical debt and quality improvements identified during the v0.8.0 review.
These are deferred until after Phase 2 (general HTML → DOCX) is complete.

---

## 1. GitHub Actions CI  ⚡ High priority

**Problem:** Tests run manually before each PR. External contributors could merge untested code.

**Fix:** Add `.github/workflows/ci.yml` — runs `pytest` on every PR and push to main. Also run on Python 3.10, 3.11, 3.12 to catch version-specific issues.

**Effort:** ~1 hour

---

## 2. `dataclasses.replace()` refactor  ⚡ High priority

**Problem:** Every `MutableParagraph` setter reconstructs `ParagraphFormatting` by listing all 12+ fields explicitly. When we added `tab_stops` in v0.8.0, we had to update 8 setters and briefly introduced a bug by missing one. This is a maintenance trap that gets worse as we add fields.

**Fix:** Replace all setter bodies with `dataclasses.replace()`:

```python
# Current — fragile, 12 lines per setter
def set_alignment(self, alignment):
    self._fmt = ParagraphFormatting(
        style_id=self._fmt.style_id,
        alignment=alignment,
        indent_left_pt=self._fmt.indent_left_pt,
        # ... 9 more fields
    )

# Better — 3 lines per setter, immune to new fields
def set_alignment(self, alignment):
    self._fmt = dataclasses.replace(self._fmt, alignment=alignment)
    return self
```

Applies to all setters in `docwow/api/paragraph.py`.

**Effort:** ~1 hour

---

## 3. CHANGELOG  ⚡ High priority

**Problem:** No changelog file. Users and contributors can't see what changed per version without digging through git log.

**Fix:** Add `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com) format. Backfill entries for v0.1.0–v0.8.0 from git history.

**Effort:** ~30 minutes

---

## 4. GitHub issue and PR templates  📋 Medium priority

**Problem:** No templates means issues arrive with no reproduction steps and PRs arrive with no description.

**Fix:** Add:
- `.github/ISSUE_TEMPLATE/bug_report.md` — docwow version, Python version, minimal reproduction
- `.github/ISSUE_TEMPLATE/feature_request.md` — use case, proposed approach
- `.github/pull_request_template.md` — what changed, test count, coverage, manual check done

**Effort:** ~30 minutes

---

## 5. Error handling at parse boundaries  📋 Medium priority

**Problem:** 27 bare `int()` calls on XML attribute values across the parsers. A corrupted or non-standard DOCX throws a cryptic `ValueError: invalid literal for int()` deep in lxml with no context.

**Fix:** Add a `DocwowParseError` exception class and wrap boundary `int()` calls:

```python
# Before
page_width_pt = twips_to_pt(int(w_val))

# After
try:
    page_width_pt = twips_to_pt(int(w_val))
except (ValueError, TypeError) as e:
    raise DocwowParseError(
        f"Invalid value {w_val!r} for w:pgSz/w:w in word/document.xml — expected integer twips"
    ) from e
```

Applies to: `docwow/parser/style_parser.py` (9 calls), `docwow/parser/body_parser.py` (12 calls), `docwow/parser/docx_parser.py` (6 calls).

**Effort:** ~2 hours

---

## 6. Style lookup optimisation  📋 Low priority

**Problem:** `css_generator.py` iterates the styles tuple on every render. O(s) per document where s = number of styles. Not a real bottleneck at typical document sizes (<100 styles) but worth fixing before the library is used on very large documents.

**Fix:** Build a `{style_id: Style}` dict at parse time on the `Document` model (or lazily in the renderer).

**Effort:** ~30 minutes

---

## 7. Type checking in CI  📋 Low priority

**Problem:** Type annotations exist throughout but are never checked. Mypy or pyright would catch type errors that tests don't.

**Fix:** Add `mypy` to dev dependencies and a `mypy` step to CI. Resolve any existing type errors.

**Effort:** ~2 hours (including fixing existing issues)

---

## Priority order

Do these after Phase 2 (v0.9.0) ships:

1. GitHub Actions CI — blocks safe external contributions
2. `dataclasses.replace()` refactor — prevents future field-addition bugs
3. CHANGELOG — backfill and maintain going forward
4. GitHub issue/PR templates — improves contribution quality
5. Error handling — improves user experience on bad input
6. Style lookup optimisation — minor perf
7. Type checking in CI — quality gate
