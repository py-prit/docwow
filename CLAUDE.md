# docwow — Claude Code Guide

This file is read automatically by Claude Code at the start of every session.
It tells Claude how to work on this codebase consistently.

## Project overview

docwow is a pure-Python DOCX ↔ HTML converter with a mutable programmatic API.
Full documentation: https://docwow.readthedocs.io

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e ".[dev,docs]"
```

## Running tests

```bash
source venv/bin/activate
pytest                            # full suite with coverage (must stay ≥ 90%)
pytest tests/models/              # single module
pytest -k test_bold               # by name
pytest --no-cov                   # skip coverage (faster iteration)
```

## Architecture

The pipeline has five layers — every feature must touch all five:

```
DOCX file
  ↓ docwow/parser/          Extracts OOXML into frozen dataclasses (docwow/models/)
  ↓ docwow/api/_convert.py  Wraps frozen models in mutable API wrappers (docwow/api/)
  ↑ docwow/api/_convert.py  _to_frozen() converts wrappers back to models
  ↓ docwow/renderer/        Renders frozen models to HTML
  ↓ docwow/html_parser/     Parses HTML back to frozen models
  ↓ docwow/writer/          Writes frozen models back to DOCX
```

Key design rule: **frozen models** (`docwow/models/`) are immutable dataclasses used
throughout the pipeline. **Mutable wrappers** (`docwow/api/`) are the user-facing API;
they call `_to_frozen()` before hitting the pipeline.

## Branching and PR rules

**Never push directly to `main`.** Every change goes through a feature branch + PR.

```bash
git checkout -b feat/<feature-name>   # always start here
# ... make changes ...
git push -u origin feat/<feature-name>
gh pr create ...
```

Branch naming: `feat/<name>` for features, `fix/<name>` for bugs, `chore/<name>` for
tooling/docs/versioning.

## What belongs on one branch

One branch = one DOCX feature, containing **all** of:
- Model changes (`docwow/models/`)
- Parser (`docwow/parser/`)
- HTML renderer (`docwow/renderer/`)
- HTML parser (`docwow/html_parser/`)
- DOCX writer (`docwow/writer/`)
- Programmatic API (`docwow/api/`)
- Tests (unit + integration + round-trip)
- Documentation (`docs/`)

Do not split a feature across multiple branches.

## Documentation rules

After **every change** — no matter how small — verify that all of the following are
consistent with the current codebase before committing:

- `README.md` — feature list, examples
- `docs/index.md` — feature bullets
- `docs/user-guide/tutorial.md` — end-to-end tutorial
- `docs/user-guide/open-api.md` — API reference guide
- `docs/api-reference/api-classes.md` — mkdocstrings entries
- `docs/html-format/data-attributes.md` — **every new `data-dw-*` attribute must be documented here**
- `docs/html-format/css-classes.md` — **every new CSS class must be documented here**
- `docs/html-format/overview.md` — CSS class summary table
- `docs/internals/architecture.md` — if the layer diagram or module map changed

Check for: stale class names, missing methods, incorrect code examples, "not yet
supported" notes that are now wrong, version refs.

### Docstring rule (enforced by tests)

Every public method and property in `docwow/api/` **must** have a docstring.
`tests/api/test_api_docstrings.py` fails if any are missing — the test suite will
catch this automatically. When adding a new `Mutable*` class or new method:

1. Add the class to `PUBLIC_CLASSES` in `test_api_docstrings.py`
2. Add a docstring to every public method and property
3. Add a `:::` entry to `docs/api-reference/api-classes.md`

## Versioning

Follow Semantic Versioning (`MAJOR.MINOR.PATCH`):

| Bump | When |
|---|---|
| `PATCH` | Bug fix, no API change |
| `MINOR` | New feature, fully backward compatible |
| `MAJOR` | Breaking public API change, or graduation to 1.0 |

Bump version in `pyproject.toml` on its own `chore/bump-X.Y.Z` branch after merging
the feature branch. Then upload to PyPI.

### On every version bump — mandatory checklist

Every `chore/bump-X.Y.Z` branch **must** include all of these:

1. **`pyproject.toml`** — update `version`
2. **`docwow/__init__.py`** — update `__version__`
3. **`CHANGELOG.md`** — add a new `## [X.Y.Z] - YYYY-MM-DD` section with Added/Changed/Fixed entries
4. **`README.md`** — verify feature table and roadmap are current
5. **`docs/index.md`** — verify feature bullets match

Never bump the version without updating CHANGELOG.md — this is how users and contributors
track what changed.

## Testing standards

Three layers of tests are expected for every feature:

1. **Unit tests** — model equality, parser output, renderer output in isolation
2. **Integration tests** — full DOCX → HTML → DOCX round-trip, verify semantic
   equivalence (same text, formatting, structure)
3. **API tests** — mutable wrapper behaviour, `_to_frozen()` correctness

Test files mirror the source layout: `tests/api/`, `tests/parser/`, `tests/renderer/`,
`tests/writer/`, `tests/models/`, `tests/html_parser/`.

## Code style

- Python 3.10+, type annotations on all public functions
- `from __future__ import annotations` at the top of every file
- Frozen dataclasses for all model classes (`docwow/models/`)
- No mutable default arguments, no global state
- Setters on mutable wrappers return `self` for chaining

## Public API conventions

Mutable wrapper classes live in `docwow/api/`. Naming pattern:
- `Mutable<Thing>` for editable wrappers (`MutableParagraph`, `MutableTable`, ...)
- `<Thing>Collection` for ordered mutable lists (`ParagraphCollection`, `RunCollection`)
- Old `<Thing>View` names are backward-compat aliases — new code uses `Mutable<Thing>`

Setters return `self` (chainable). All public methods have docstrings.

## CI and infra rules

The project uses GitHub Actions CI (`.github/workflows/ci.yml`). It runs on every PR and
push to `main`. **CI must be green before merging any PR** — no exceptions.

CI checks:
- `pytest` with coverage on Python 3.10, 3.11, 3.12
- Coverage must stay ≥ 90% (`--cov-fail-under=90` in pyproject.toml)

If CI fails on a PR, investigate and fix the underlying issue. Never bypass with
`--no-verify` or skip the coverage check.

### Maintaining CHANGELOG.md

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com) format.

- Every merged feature/fix PR adds an entry under `## [Unreleased]`
- On version bump, rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD` and add a fresh `[Unreleased]` section above it
- Categories: `Added`, `Changed`, `Fixed`, `Removed`, `Deprecated`

## Useful commands

```bash
# Generate test fixtures
python tests/fixtures/generate_fixtures.py
python tests/fixtures/generate_showcase.py

# Build docs locally
mkdocs serve   # http://127.0.0.1:8000

# Create a PR (after gh auth login)
gh pr create --title "..." --body "..."
```
