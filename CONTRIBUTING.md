# Contributing to docwow

Thank you for your interest in contributing! docwow is a pure-Python DOCX ↔ HTML converter and every contribution — bug reports, feature requests, and pull requests — is welcome.

## Table of contents

- [Reporting issues](#reporting-issues)
- [Development setup](#development-setup)
- [Architecture overview](#architecture-overview)
- [Adding a new feature](#adding-a-new-feature)
- [Testing requirements](#testing-requirements)
- [Documentation requirements](#documentation-requirements)
- [Pull request process](#pull-request-process)
- [Code style](#code-style)

---

## Reporting issues

Open an issue at **https://github.com/py-prit/docwow/issues** with:

- A minimal reproducible example (a DOCX file or HTML snippet)
- What you expected vs what you got
- Your Python version and docwow version (`python -c "import docwow; print(docwow.__version__)"`)

If you hit a warning like *"this feature is not yet supported"*, please open an issue — that warning is a direct signal that the feature is on the roadmap and a contributor is needed.

---

## Development setup

```bash
git clone https://github.com/py-prit/docwow.git
cd docwow
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e ".[dev,docs]"
pytest                            # full suite — must stay ≥ 90% coverage
```

---

## Architecture overview

The pipeline has five layers. Every feature must touch all five:

```
DOCX file
  ↓ docwow/parser/          Extracts OOXML into frozen dataclasses (docwow/models/)
  ↓ docwow/api/_convert.py  Wraps frozen models in mutable API wrappers (docwow/api/)
  ↑ docwow/api/_convert.py  _to_frozen() converts wrappers back to models
  ↓ docwow/renderer/        Renders frozen models to HTML
  ↓ docwow/html_parser/     Parses HTML back to frozen models
  ↓ docwow/writer/          Writes frozen models back to DOCX
```

**Frozen models** (`docwow/models/`) are immutable dataclasses used throughout the pipeline. **Mutable wrappers** (`docwow/api/`) are the user-facing API. Users work with mutable wrappers; the pipeline always uses frozen models.

---

## Adding a new feature

Each feature = one branch = one PR. Every PR must include all five layers together — never split a feature across branches.

### 1. Pick a branch name

```bash
git checkout -b feat/<feature-name>   # new DOCX/HTML feature
git checkout -b fix/<bug-name>        # bug fix
git checkout -b chore/<task>          # tooling, docs, versioning
```

### 2. Implement all five layers

| Layer | File(s) | What to add |
|---|---|---|
| Model | `docwow/models/` | Frozen dataclass field(s) |
| Parser | `docwow/parser/` | OOXML → model |
| Renderer | `docwow/renderer/` | Model → HTML (`data-dw-*` attrs + CSS) |
| HTML parser | `docwow/html_parser/` | HTML `data-dw-*` attrs → model |
| Writer | `docwow/writer/` | Model → OOXML |
| API | `docwow/api/` | Mutable wrapper + setter + `_to_frozen()` |

### 3. Write tests (three tiers)

1. **Unit tests** — model fields, parser output, renderer output in isolation
2. **Round-trip tests** — DOCX → HTML → DOCX, verify semantic equivalence
3. **API tests** — mutable wrapper behaviour, `_to_frozen()` correctness

Test files mirror source layout: `tests/api/`, `tests/parser/`, `tests/renderer/`, `tests/writer/`, `tests/models/`, `tests/html_parser/`.

### 4. Update documentation

Every PR must update (where applicable):

| File | When to update |
|---|---|
| `README.md` | New feature in supported table |
| `docs/index.md` | Feature bullet |
| `docs/user-guide/open-api.md` | API usage example |
| `docs/html-format/data-attributes.md` | Every new `data-dw-*` attribute |
| `docs/html-format/css-classes.md` | Every new CSS class |

### 5. Docstring rule

Every public method and property in `docwow/api/` must have a docstring. The test suite enforces this: `tests/api/test_api_docstrings.py` will fail if any are missing.

---

## Testing requirements

```bash
pytest                    # full suite with coverage (must stay ≥ 90%)
pytest --no-cov -x -q    # fast iteration during development
pytest tests/parser/      # run a single module
pytest -k test_bold       # run tests matching a name
```

Coverage must remain at or above **90%** — CI will fail if it drops below.

---

## Documentation requirements

Build the docs locally to verify your changes render correctly:

```bash
mkdocs serve   # preview at http://127.0.0.1:8000
```

Full documentation is at [docwow.readthedocs.io](https://docwow.readthedocs.io).

---

## Pull request process

1. Open a PR against `main`
2. Title format: `feat: ...`, `fix: ...`, or `chore: ...`
3. PR description should explain what changed and why — reference any related issue
4. All tests must pass and coverage must stay ≥ 90%
5. One PR per feature — do not bundle unrelated changes

---

## Code style

- Python 3.10+, type annotations on all public functions
- `from __future__ import annotations` at the top of every file
- Frozen dataclasses for all model classes (`docwow/models/`)
- No mutable default arguments, no global state
- Setters on mutable wrappers return `self` for method chaining
- No comments unless the *why* is non-obvious
- No docstrings on private/internal functions

---

## Roadmap

See the [README roadmap section](README.md#roadmap) for planned features and effort estimates. Features marked with an estimated effort are good starting points for first-time contributors.
