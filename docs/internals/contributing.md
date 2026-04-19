# Contributing

## Setup

```bash
git clone https://github.com/py-prit/docwow
cd docwow
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,docs]"
```

## Running tests

```bash
pytest                          # run all tests with coverage
pytest tests/models/            # run a specific module
pytest -k test_bold             # run tests matching a name
pytest --no-cov                 # skip coverage (faster)
```

Coverage must stay at or above 90%. The CI gate enforces this.

## Adding a feature

1. Add or update the model in `docwow/models/` if new data needs to be carried through the pipeline
2. Update the DOCX parser (`docwow/parser/`) to extract the new data from OOXML
3. Update the HTML renderer (`docwow/renderer/`) to emit the new `data-dw-*` attribute and CSS
4. Update the HTML parser (`docwow/html_parser/`) to read the attribute back from HTML
5. Update the DOCX writer (`docwow/writer/`) to write the new data back to OOXML
6. Add tests at each layer
7. Update `docs/html-format/data-attributes.md` if you added a new `data-dw-*` attribute

## Running the docs locally

```bash
pip install -e ".[docs]"
mkdocs serve
# open http://127.0.0.1:8000
```

## Regenerating the showcase

```bash
python tests/fixtures/generate_showcase.py
python -c "import docwow; open('tests/fixtures/showcase.html','w').write(docwow.to_html('tests/fixtures/showcase.docx'))"
```

## Versioning

docwow follows [Semantic Versioning](https://semver.org): `MAJOR.MINOR.PATCH`.

| Bump | When | Examples |
|---|---|---|
| `PATCH` | Bug fix, no API or feature change | Parser crash on edge-case DOCX, wrong CSS emitted, incorrect XML written |
| `MINOR` | New DOCX feature added, fully backward compatible | Each new feature: footnotes, bookmarks, table editing, comments |
| `MAJOR` | Breaking public API change, or graduation to stable 1.0 | Renaming a public method, changing a model field type, dropping a Python version |

**Patch releases** (`1.0.x`) can be cut at any time from `main` for confirmed bugs. A direct commit with a test reproducing the bug is sufficient.

**Minor releases** (`1.x.0`) follow the standard branch workflow: one branch per DOCX feature (`feat/<feature-name>`), containing conversion (parser + renderer + html_parser + writer), API, tests, and documentation all together.

**Major releases** (`2.0.0+`) require breaking public API changes. These are rare — the goal is to keep the public API stable across all 1.x releases.

## Code style

- Python 3.10+, type annotations on all public functions
- `from __future__ import annotations` at the top of every file
- Frozen dataclasses for all model classes
- No mutable default arguments
- No global state
