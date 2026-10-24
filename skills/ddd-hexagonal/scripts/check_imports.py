#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Fallback architecture check for languages without a dependency-rule tool.

Usage:
    uv run check_imports.py --dir src/domain --forbid REGEX [--forbid REGEX ...]
                            [--ext .php --ext .go]

Scans every file under --dir for import-style lines (import, from, use, require,
using, include, #include) that match any --forbid regex. Prints each hit and exits 1
if there is any. Example, keeping a PHP domain free of frameworks:

    uv run check_imports.py --dir src/Domain --ext .php --forbid "PDO|Slim\\\\|Twig\\\\"

Prefer a real tool where one exists (see the language reference files); this check
only sees import lines, not fully qualified names used inline.
"""
import argparse
import re
import sys
from pathlib import Path

IMPORT_LINE = re.compile(r"^\s*(import|from|use|require|require_once|using|include|#include)\b")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--forbid", action="append", required=True)
    ap.add_argument("--ext", action="append", default=[])
    a = ap.parse_args()

    patterns = [re.compile(p) for p in a.forbid]
    root = Path(a.dir)
    if not root.exists():
        print(f"error: folder not found: {root}")
        return 1

    hits = 0
    for f in sorted(root.rglob("*")):
        if not f.is_file() or (a.ext and f.suffix not in a.ext):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if IMPORT_LINE.match(line) and any(p.search(line) for p in patterns):
                print(f"{f}:{n}: {line.strip()}")
                hits += 1
    print(f"{hits} forbidden import(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
