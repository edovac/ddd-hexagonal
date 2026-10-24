#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""List every place a rule ID or use case ID is mentioned: documents, tests and code.

Usage:
    uv run rule_impact.py AL-06 [BK-01 UC-02 ...] [--root .]

Prints file:line for each mention, grouped as docs (*.md), tests (paths containing
test/tests/spec) and code (everything else), skipping .git, virtual environments,
dependency folders and build output. Use it before changing a rule so the impact
analysis starts from facts instead of memory.
"""
import argparse
import os
import re
import sys
from pathlib import Path

SKIP = {".git", ".venv", "venv", "node_modules", "vendor", "target", "build", "dist",
        "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".import_linter_cache", ".idea", ".vscode"}
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc", ".class", ".jar", ".lock", ".ico", ".woff", ".woff2"}


def group(path: Path) -> str:
    parts = {p.lower() for p in path.parts}
    if path.suffix == ".md":
        return "docs"
    if parts & {"test", "tests", "spec", "specs", "__tests__"} or ".test." in path.name or "_test" in path.name:
        return "tests"
    return "code"


def files(root: Path):
    """Text-like files under root, without descending into skipped folders."""
    for d, dirs, names in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        for name in sorted(names):
            f = Path(d) / name
            if f.suffix.lower() not in BINARY:
                yield f


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    patterns = {i: re.compile(rf"(?<![A-Za-z0-9-]){re.escape(i)}(?![0-9])") for i in a.ids}
    root = Path(a.root)
    found = {i: {"docs": [], "tests": [], "code": []} for i in a.ids}
    for f in files(root):
        try:
            lines = f.read_text(encoding="utf-8", errors="strict").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        g = group(f.relative_to(root))
        for n, line in enumerate(lines, 1):
            for i, pat in patterns.items():
                if pat.search(line):
                    found[i][g].append(f"{f.relative_to(root).as_posix()}:{n}: {line.strip()[:110]}")
    for i in a.ids:
        print(f"== {i}")
        for g in ("docs", "tests", "code"):
            print(f"  {g} ({len(found[i][g])})")
            for item in found[i][g]:
                print("    " + item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
