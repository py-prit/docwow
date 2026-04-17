"""
Stress test docwow against real-world DOCX files downloaded from open-source repos.

Sources:
  - Apache POI test suite  (apache/poi, test-data/document/)
  - Mammoth test suite     (mwilliamson/mammoth.py, tests/)
  - python-docx test suite (python-openxml/python-docx, tests/)

Usage:
    python scripts/stress_test.py           # download + run all sources
    python scripts/stress_test.py --cached  # skip download, use existing files
    python scripts/stress_test.py --limit 20  # cap files per source
"""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

import requests

STRESS_DIR = Path(__file__).parent.parent / "tests" / "stress_files"

SOURCES = [
    {
        "name": "Apache POI",
        "api_url": "https://api.github.com/repos/apache/poi/contents/test-data/document",
        "raw_base": "https://raw.githubusercontent.com/apache/poi/trunk/test-data/document",
        "subdir": "poi",
        "recursive": False,
    },
    {
        "name": "python-docx",
        "api_url": "https://api.github.com/repos/python-openxml/python-docx/contents/features/steps/test_files",
        "raw_base": "https://raw.githubusercontent.com/python-openxml/python-docx/master/features/steps/test_files",
        "subdir": "python-docx",
        "recursive": False,
    },
]


def fetch_docx_urls(api_url: str, raw_base: str, limit: int) -> list[tuple[str, str]]:
    """Return list of (filename, download_url) for .docx files in a GitHub directory."""
    resp = requests.get(api_url, timeout=15)
    resp.raise_for_status()
    files = resp.json()
    results = []
    for entry in files:
        if isinstance(entry, dict) and entry.get("name", "").lower().endswith(".docx"):
            name = entry["name"]
            url = f"{raw_base}/{name}"
            results.append((name, url))
            if len(results) >= limit:
                break
    return results


def download_file(url: str, dest: Path) -> bool:
    """Download a file to dest. Returns True on success."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"    [download error] {e}")
        return False


def download_all(limit: int) -> None:
    """Download DOCX files from all sources into tests/stress_files/."""
    STRESS_DIR.mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        subdir = STRESS_DIR / source["subdir"]
        subdir.mkdir(exist_ok=True)
        print(f"\nFetching file list: {source['name']} ...")
        try:
            files = fetch_docx_urls(source["api_url"], source["raw_base"], limit)
        except Exception as e:
            print(f"  [error listing files] {e}")
            continue

        print(f"  Found {len(files)} .docx files (limit={limit})")
        for name, url in files:
            dest = subdir / name
            if dest.exists():
                print(f"  [skip] {name} (already downloaded)")
                continue
            print(f"  Downloading {name} ...", end=" ", flush=True)
            ok = download_file(url, dest)
            if ok:
                print("ok")
            time.sleep(0.1)  # be polite to GitHub


def run_stress_test() -> dict:
    """Run docwow.to_html() on every downloaded file. Returns result summary."""
    import docwow

    results = {"passed": [], "failed": [], "skipped": []}

    docx_files = sorted(STRESS_DIR.rglob("*.docx"))
    if not docx_files:
        print("No DOCX files found. Run without --cached first to download them.")
        return results

    print(f"\nRunning docwow.to_html() on {len(docx_files)} files...\n")
    col_w = max(len(str(f.relative_to(STRESS_DIR))) for f in docx_files) + 2

    for path in docx_files:
        label = str(path.relative_to(STRESS_DIR))
        try:
            html = docwow.to_html(str(path))
            # Basic sanity: output should be a non-empty string
            if not html or not isinstance(html, str):
                raise ValueError("to_html() returned empty/non-string output")
            print(f"  PASS  {label}")
            results["passed"].append(label)
        except Exception:
            tb = traceback.format_exc().strip().splitlines()
            # Show just the last two lines of the traceback (exception + message)
            short = " | ".join(tb[-2:]) if len(tb) >= 2 else tb[-1]
            print(f"  FAIL  {label}")
            print(f"        {short}")
            results["failed"].append({"file": label, "error": traceback.format_exc()})

    return results


def print_summary(results: dict) -> None:
    total = len(results["passed"]) + len(results["failed"])
    passed = len(results["passed"])
    failed = len(results["failed"])

    print("\n" + "=" * 60)
    print(f"STRESS TEST SUMMARY")
    print("=" * 60)
    print(f"  Total files : {total}")
    print(f"  Passed      : {passed}")
    print(f"  Failed      : {failed}")

    if results["failed"]:
        print(f"\nFailed files:")
        for entry in results["failed"]:
            print(f"\n  {entry['file']}")
            for line in entry["error"].strip().splitlines():
                print(f"    {line}")

    print()
    if failed == 0:
        print("All files passed.")
    else:
        pct = passed / total * 100 if total else 0
        print(f"{pct:.0f}% pass rate ({passed}/{total})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test docwow with real-world DOCX files")
    parser.add_argument("--cached", action="store_true", help="Skip download, use existing files")
    parser.add_argument("--limit", type=int, default=50, help="Max files to download per source (default: 50)")
    args = parser.parse_args()

    if not args.cached:
        download_all(limit=args.limit)

    results = run_stress_test()
    print_summary(results)

    sys.exit(1 if results["failed"] else 0)


if __name__ == "__main__":
    main()
