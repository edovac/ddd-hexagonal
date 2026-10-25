#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Fallback architecture check for languages without a dependency-rule tool.

Usage:
    uv run check_imports.py --dir src/domain --forbid REGEX [--forbid REGEX ...]
                            [--ext .php --ext .go] [--baseline FILE | --write-baseline FILE]

Scans every file under --dir for import-style lines (import, from, use, require,
using, include, #include) that match any --forbid regex. Prints each hit and exits 1
if there is any. Example, keeping a PHP domain free of frameworks:

    uv run check_imports.py --dir src/Domain --ext .php --forbid "PDO|Slim\\\\|Twig\\\\"

For existing code that already breaks the rule, record the current hits once with
--write-baseline FILE (exit 0), then run with --baseline FILE: hits listed there are
reported as known and pass, any other hit fails. An entry is the file path and the import
line without its number, so moving code inside a file keeps it known. Entries no longer
found are reported as stale, so the baseline can only shrink.

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
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--baseline", help="file of known hits that do not fail the check")
    group.add_argument("--write-baseline", help="write the current hits to this file and exit 0")
    a = ap.parse_args()

    patterns = [re.compile(p) for p in a.forbid]
    root = Path(a.dir)
    if not root.exists():
        print(f"error: folder not found: {root}")
        return 1

    hits: list[tuple[str, int, str]] = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or (a.ext and f.suffix not in a.ext):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if IMPORT_LINE.match(line) and any(p.search(line) for p in patterns):
                hits.append((f.as_posix(), n, line.strip()))

    if a.write_baseline:
        entries = sorted({f"{f}: {line}" for f, _, line in hits})
        Path(a.write_baseline).write_text("".join(e + "\n" for e in entries), encoding="utf-8")
        print(f"{len(entries)} known import(s) written to {a.write_baseline}")
        return 0

    known: set[str] = set()
    if a.baseline:
        base = Path(a.baseline)
        if not base.exists():
            print(f"error: baseline not found: {base}")
            return 1
        known = {l.strip() for l in base.read_text(encoding="utf-8").splitlines() if l.strip()}

    new = 0
    found: set[str] = set()
    for f, n, line in hits:
        entry = f"{f}: {line}"
        found.add(entry)
        if entry in known:
            continue
        print(f"{f}:{n}: {line}")
        new += 1
    for entry in sorted(known - found):
        print(f"stale baseline entry (no longer found, remove it): {entry}")
    if a.baseline:
        print(f"{new} forbidden import(s), {len(found & known)} known in the baseline")
    else:
        print(f"{new} forbidden import(s)")
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
