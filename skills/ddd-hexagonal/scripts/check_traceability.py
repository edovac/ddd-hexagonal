#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Check that business rule IDs, use cases and tests agree.

Usage:
    uv run check_traceability.py --docs docs [--rules docs/business-rules.md]
                                 [--use-cases docs/use-cases.md] [--tests tests]
                                 [--strict]

What it checks
  * Rule IDs used in any document but not defined in the rules file (error).
  * Rules defined but never referenced by a use case or another document (warning).
  * Rules cited in no test file (warning, error with --strict).
  * Use cases that list no rule IDs (warning).

A rule is defined by a table row that starts with its ID, e.g. "| AL-06 | ... |".
Prefixes are learned from those rows, so ordinary tokens such as SHA-256 are ignored.
A range such as "AL-02 to AL-07" or "AL-02…AL-07" counts every ID in it.
Both ends must carry the prefix: "AL-02 to 07" counts only AL-02.
A test cites a rule when the ID appears anywhere in a file under --tests.
Exit code: 0 clean, 1 errors found.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

DEF_ROW = re.compile(r"^\|\s*([A-Z]{2,5})-(\d{1,3})\s*\|", re.M)
UC_ROW = re.compile(r"^\|\s*(UC-\d{1,3})\s*\|(.*)$", re.M)


ROW = re.compile(r"^\|\s*([A-Z]{2,5}-\d{1,3}|UC-\d{1,3})\s*\|(.*)$", re.M)
MARKER = re.compile(r"\((removed|superseded)", re.I)


def rows(text: str) -> dict[str, str]:
    """ID -> rest of the table row, for rule and use case rows."""
    out: dict[str, str] = {}
    for rid, rest in ROW.findall(text):
        key = rid if "-" not in rid else f"{rid.split('-')[0]}-{rid.split('-')[1].zfill(2)}"
        out[key] = rest
    return out


def git_show(path: Path, ref: str) -> str | None:
    """Content of path at ref, or None when not in a git repository or not present at ref."""
    try:
        r = subprocess.run(["git", "show", f"{ref}:./{path.name}"], cwd=path.resolve().parent,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def expand(text: str, prefixes: set[str]) -> set[str]:
    ids: set[str] = set()
    alt = "|".join(sorted(prefixes))
    if not alt:
        return ids
    for m in re.finditer(rf"\b({alt})-(\d{{1,3}})\b", text):
        ids.add(f"{m.group(1)}-{m.group(2).zfill(2)}")
    # Both ends carry the prefix, so "AL-02 - 10 minutes" is not read as AL-02..AL-10.
    rng = rf"\b({alt})-(\d{{1,3}})\s*(?:…|\.\.\.|–|-|to)\s*\1-(\d{{1,3}})\b"
    for m in re.finditer(rng, text):
        lo, hi = int(m.group(2)), int(m.group(3))
        if lo <= hi <= lo + 60:
            for i in range(lo, hi + 1):
                ids.add(f"{m.group(1)}-{str(i).zfill(2)}")
    return ids


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--rules", default=None)
    ap.add_argument("--use-cases", default=None)
    ap.add_argument("--tests", default=None)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--since", default="HEAD", help="git ref to compare IDs against (default HEAD)")
    ap.add_argument("--no-history", action="store_true", help="skip the ID-stability comparison")
    a = ap.parse_args()

    docs = Path(a.docs)
    rules_file = Path(a.rules) if a.rules else docs / "business-rules.md"
    uc_file = Path(a.use_cases) if a.use_cases else docs / "use-cases.md"
    if not rules_file.exists():
        print(f"error: rules file not found: {rules_file}")
        return 1

    rules_text = read(rules_file)
    defined = {f"{p}-{n.zfill(2)}" for p, n in DEF_ROW.findall(rules_text)}
    prefixes = {i.split("-")[0] for i in defined}
    print(f"{len(defined)} rules defined, prefixes: {', '.join(sorted(prefixes))}")

    errors: list[str] = []
    warnings: list[str] = []

    # ID stability: an ID defined at --since must still be there, or be marked (removed)/(superseded ...).
    now_rows = rows(rules_text)
    if uc_file.exists():
        now_rows.update(rows(read(uc_file)))
    seen_ids = [f"{p}-{n.zfill(2)}" for p, n in DEF_ROW.findall(rules_text)]
    for dup in sorted({i for i in seen_ids if seen_ids.count(i) > 1}):
        errors.append(f"{dup} is defined more than once (an ID must never be reused)")
    if not a.no_history:
        old_text = git_show(rules_file, a.since)
        old_uc = git_show(uc_file, a.since) if uc_file.exists() else None
        if old_text is None and old_uc is None:
            print(f"note: no git history for the rules file at {a.since}; ID-stability check skipped")
        else:
            old_rows = rows(old_text or "")
            old_rows.update(rows(old_uc or ""))
            for oid in sorted(old_rows):
                if oid not in now_rows:
                    errors.append(f"{oid} existed at {a.since} but is gone; mark it '(removed)' or '(superseded by ...)' instead of deleting it")
                elif MARKER.search(old_rows[oid]) and not MARKER.search(now_rows[oid]):
                    errors.append(f"{oid} was marked removed/superseded at {a.since} and is live again; use a new ID")
    removed_now = {rid for rid, rest in now_rows.items() if MARKER.search(rest)}

    referenced: set[str] = set()
    for md in sorted(docs.rglob("*.md")):
        text = read(md)
        ids = expand(text, prefixes)
        if md.resolve() == rules_file.resolve():
            ids -= {f"{p}-{n.zfill(2)}" for p, n in DEF_ROW.findall(text)}
            ids = {i for i in ids if i not in defined}
        else:
            referenced |= ids
        for i in sorted(ids - defined):
            errors.append(f"{md.name}: {i} is used but not defined")

    use_cases = {}
    uc_rest = {}
    if uc_file.exists():
        for uc, rest in UC_ROW.findall(read(uc_file)):
            use_cases[uc] = expand(rest, prefixes)
            uc_rest[uc] = rest
        for uc, ids in use_cases.items():
            if not ids and "none" not in uc_rest[uc].lower():
                warnings.append(f"{uc} lists no rule IDs (write 'none' if that is intended)")
        print(f"{len(use_cases)} use cases")

    for rid in sorted(removed_now & referenced):
        warnings.append(f"{rid} is marked removed/superseded but is still cited by another document")
    for r in sorted(defined - referenced - removed_now):
        warnings.append(f"{r} is not referenced by any other document")

    if a.tests:
        tests = Path(a.tests)
        cited: set[str] = set()
        if tests.exists():
            for f in tests.rglob("*"):
                if f.is_file() and f.suffix not in {".png", ".jpg", ".gif", ".pdf", ".zip"}:
                    cited |= expand(read(f), prefixes)
        else:
            warnings.append(f"tests folder not found: {tests}")
        missing = sorted(defined - cited)
        target = errors if a.strict else warnings
        for r in missing:
            target.append(f"{r} has no test")
        print(f"{len(defined) - len(missing)}/{len(defined)} rules cited in tests")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
