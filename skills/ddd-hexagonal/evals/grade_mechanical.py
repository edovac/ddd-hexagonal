#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Grade the mechanical assertions of an eval run with code instead of an agent.

Usage:
    uv run grade_mechanical.py <eval-name> <project-dir> [--outputs DIR]
        [--env KEY=VALUE ...] [--mysql-container NAME] [--mysql-password PW] [--out FILE]

<project-dir> is the project the run worked in (made by setup_fixture.py, or an empty git
repository for bootstrap-invoicing). --outputs is the run's outputs folder (log.md, questions.md).
--env values go to every command the script runs, for example
`--env DATABASE_URL=postgresql://postgres:test@localhost:5433/mydb`; without DATABASE_URL the
integration tests and the stored-booking probe are reported as not run. --mysql-container names a
running mysql:8 container (root password --mysql-password, default "test") for the write-path probe
of change-db-swap.
The DATABASE_URL must follow the project's own convention (read its tests/integration/conftest.py);
the change-db-swap runs of this repository insist on a database name ending in _test.

Prints JSON: for each assertion of the eval that code can decide, `passed` true/false and the
evidence; `needs_judgment` lists the assertions it cannot decide (with numbers that help, in
`evidence`). A grader agent then reads only those. The script never changes the project except for
the caches that running its tools creates.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EVALS = Path(__file__).resolve().parent
COMMITS_AT_START = {"bootstrap-invoicing": 0, "build-book-room": 1, "review-returns-docs": 1,
                    "change-booking-limits": 2, "change-new-use-case": 2, "change-db-swap": 2,
                    "adopt-library-loans": 1, "adopt-confirmation": 1,
                    "fix-double-return": 2}
SKIP_DIRS = {".venv", "__pycache__", ".git", "node_modules", ".mypy_cache", ".ruff_cache", ".pytest_cache"}
WEB = r"fastapi|flask|django|starlette|aiohttp|uvicorn|tornado|bottle|sanic|APIRouter|@app\.(get|post|put|delete)"
DRIVERS = r"psycopg|pymysql|mysql|sqlalchemy|asyncpg|sqlite3|django|flask|fastapi|requests|httpx|boto3"
CLOCK = r"uuid4|uuid1|datetime\.now|datetime\.utcnow|date\.today|time\.time\(|\brandom\b|secrets\."
CONCURRENCY = r"threading|Thread\(|ThreadPool|concurrent\.futures|asyncio\.gather|multiprocessing|pytest-xdist"
RULE_ROW = re.compile(r"^\|\s*([A-Z]{2,5}-\d{1,3})\s*\|(.*)$", re.M)
UC_ROW = re.compile(r"^\|\s*(UC-\d{1,3})\s*\|(.*)$", re.M)

CHECKS: dict[str, list] = {}


def check(eval_name: str, key: str):
    """Register a function (ctx) -> (passed | None, evidence) for the assertion starting with `key`."""
    def deco(fn):
        CHECKS.setdefault(eval_name, []).append((key, fn))
        return fn
    return deco


class Ctx:
    def __init__(self, eval_name: str, project: Path, outputs: Path | None, env: dict[str, str],
                 mysql_container: str | None, mysql_password: str) -> None:
        self.eval_name, self.project, self.outputs = eval_name, project, outputs
        self.extra_env = env
        base = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}  # uv would warn that it differs from the project's .venv
        self.env = {**base, "UV_LINK_MODE": "copy", **env}
        self.mysql_container, self.mysql_password = mysql_container, mysql_password
        self._cache: dict[str, tuple[int, str]] = {}

    def sh(self, cmd: list[str], timeout: int = 600, cwd: Path | None = None, stdin: str | None = None):
        r = subprocess.run(cmd, cwd=cwd or self.project, env=self.env, capture_output=True, text=True,
                           errors="replace", timeout=timeout, input=stdin)
        return r.returncode, (r.stderr + r.stdout).strip()  # stdout last: its final line is the summary

    def tool(self, name: str, cmd: list[str]) -> tuple[int, str]:
        if name not in self._cache:
            self._cache[name] = self.sh(cmd)
        return self._cache[name]

    def git(self, *args: str) -> tuple[int, str]:
        return self.sh(["git", *args])

    def head_text(self, rel: str) -> str | None:
        rc, out = self.git("show", f"HEAD:{rel}")
        return out if rc == 0 else None

    def read(self, rel: str) -> str:
        p = self.project / rel
        return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""

    def files(self, *globs: str) -> list[Path]:
        found: list[Path] = []
        for g in globs:
            for p in sorted(self.project.glob(g)):
                if p.is_file() and not (SKIP_DIRS & set(p.relative_to(self.project).parts)):
                    found.append(p)
        return found

    def docs_text(self) -> str:
        return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in self.files("docs/*.md"))

    def output_text(self, name: str) -> str:
        return (self.outputs / name).read_text(encoding="utf-8", errors="replace") if self.outputs and (self.outputs / name).is_file() else ""

    @property
    def has_pyproject(self) -> bool:
        return (self.project / "pyproject.toml").is_file()

    def domain_dirs(self, layer: str) -> list[Path]:
        return [p for p in self.project.glob(f"src/*/{layer}") if p.is_dir()]


def grep(paths: list[Path], pattern: str, flags: int = re.I) -> list[str]:
    rx = re.compile(pattern, flags)
    hits = []
    for p in paths:
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if rx.search(line):
                hits.append(f"{p.name}:{n}: {line.strip()[:100]}")
    return hits


def py_files(dirs: list[Path]) -> list[Path]:
    return [f for d in dirs for f in sorted(d.rglob("*.py")) if "__pycache__" not in f.parts]


# ---- shared checks -------------------------------------------------------------------------------

def branch_and_commits(ctx: Ctx):
    rc, branch = ctx.git("branch", "--show-current")
    rc2, count = ctx.git("rev-list", "--all", "--count")
    commits = int(count) if rc2 == 0 and count.isdigit() else 0
    expected = COMMITS_AT_START[ctx.eval_name]
    ok = branch not in ("main", "master", "") and commits == expected
    return ok, f"branch={branch!r}, commits in repository={commits} (fixture starts with {expected})"


def run_unit(ctx: Ctx):
    if not (ctx.project / "tests" / "unit").is_dir():
        return False, "no tests/unit folder"
    rc, out = ctx.tool("unit", ["uv", "run", "pytest", "tests/unit", "-q"])
    return rc == 0, out.splitlines()[-1] if out else "no output"


def run_integration(ctx: Ctx):
    if "DATABASE_URL" not in ctx.extra_env:
        return None, "not run: pass --env DATABASE_URL=..."
    rc, out = ctx.tool("integration", ["uv", "run", "pytest", "tests/integration", "-q"])
    last = out.splitlines()[-1] if out else "no output"
    if rc != 0 and re.search(r"\berrors?\b", last) and not re.search(r"\bfailed\b", last):
        # Errors without failures come from fixtures, usually a DATABASE_URL the project does not accept.
        return None, f"integration tests could not set up ({last}); check the connection convention in the project's conftest or CLAUDE.md"
    return rc == 0, last


def traceability(ctx: Ctx, history: bool = True):
    script = "tools/check_traceability.py"
    if not (ctx.project / script).is_file():
        return False, "tools/check_traceability.py missing"
    args = ["uv", "run", script, "--docs", "docs", "--tests", "tests"] + ([] if history else ["--no-history"])
    rc, out = ctx.tool(f"trace-{history}", args)
    errors = [l for l in out.splitlines() if l.startswith("error:")]
    return rc == 0, f"exit {rc}; {len(errors)} error(s)" + (": " + "; ".join(errors[:3]) if errors else "")


def domain_forbidden(ctx: Ctx, pattern: str, layers=("domain",)):
    dirs = [d for layer in layers for d in ctx.domain_dirs(layer)]
    if not dirs:
        return False, "no src/*/domain folder"
    hits = grep(py_files(dirs), pattern)
    return not hits, f"{len(hits)} hit(s)" + (": " + "; ".join(hits[:4]) if hits else "")


def dependency_lists(text: str) -> str:
    """Only the dependency arrays of a pyproject, so contract names and comments are not read as packages."""
    return "\n".join(re.findall(r"^\s*(?:dependencies|dev|test)\s*=\s*\[(.*?)\]", text, re.M | re.S))


def pyproject_deps(text: str) -> set[str]:
    return set(re.findall(r'"([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?[<>=!~ ][^"]*"', text))


def rule_ids(text: str) -> set[str]:
    return {m[0] for m in RULE_ROW.findall(text)}


def section(text: str, heading: str) -> str:
    m = re.search(rf"^##+\s*{heading}.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1) if m else ""


def tagged_tests(ctx: Ctx) -> list[str]:
    out = []
    for f in ctx.files("tests/**/*.py"):
        tags = re.findall(r"@rule\s+([A-Z]{2,5}-\d{1,3}(?:[ ,]+[A-Z]{2,5}-\d{1,3})*)", f.read_text(errors="replace"))
        for t in tags:
            out.append(f"{f.name}: {t}")
    return out


# ---- bootstrap-invoicing ----------------------------------------------------------------------------

@check("bootstrap-invoicing", "Business rules are in a table")
def _(ctx):
    text = ctx.docs_text()
    ids = rule_ids(text)
    return len(ids) >= 5, f"{len(ids)} rule rows with an ID"


@check("bootstrap-invoicing", "Rules that can fail carry")
def _(ctx):
    rows = [r for _, r in RULE_ROW.findall(ctx.read("docs/business-rules.md") or ctx.docs_text())]
    coded = [r for r in rows if re.search(r"`[a-z][a-z0-9_]{3,}`", r)]
    return None, f"{len(coded)} of {len(rows)} rules have a snake_case code in backticks"


@check("bootstrap-invoicing", "Every use case lists the rule IDs")
def _(ctx):
    ok, ev = traceability(ctx, history=False)
    out = ctx._cache.get("trace-False", (1, ""))[1]
    return ok and "lists no rule IDs" not in out, ev + ("; some use case lists no rules" if "lists no rule IDs" in out else "")


@check("bootstrap-invoicing", "Functional spec, domain model")
def _(ctx):
    need = ["docs/functional-spec.md", "docs/domain-model.md", "docs/technical-spec.md", "CLAUDE.md"]
    missing = [n for n in need if not (ctx.project / n).is_file()]
    rules = (ctx.project / "docs/business-rules.md").is_file()
    ucs = (ctx.project / "docs/use-cases.md").is_file()
    merged = (rules or ucs) and bool(UC_ROW.findall(ctx.docs_text())) and bool(RULE_ROW.findall(ctx.docs_text()))
    return not missing and merged, f"missing={missing}, business-rules.md={rules}, use-cases.md={ucs}"


@check("bootstrap-invoicing", "No application source code")
def _(ctx):
    code = []
    for f in ctx.files("src/**/*", "app/**/*", "lib/**/*"):
        if f.suffix in (".py", ".ts", ".js", ".php", ".java", ".kt", ".go") and f.read_text(errors="replace").strip():
            code.append(str(f.relative_to(ctx.project)))
    return not code, f"{len(code)} non-empty source file(s)" + (": " + ", ".join(code[:5]) if code else "")


@check("bootstrap-invoicing", "CLAUDE.md contains")
def _(ctx):
    t = ctx.read("CLAUDE.md").lower()
    parts = {"branch rule": "branch" in t and "main" in t, "dependency approval": "dependenc" in t and ("approv" in t or "ask" in t),
             "test first": "test first" in t or "test-first" in t, "pointers": "docs/" in t}
    return all(parts.values()), ", ".join(f"{k}={'yes' if v else 'NO'}" for k, v in parts.items())


@check("bootstrap-invoicing", "Technical spec names pytest")
def _(ctx):
    t = ctx.read("docs/technical-spec.md").lower()
    parts = {"pytest": "pytest" in t, "architecture check": "import-linter" in t or "import linter" in t or "lint-imports" in t,
             "layout": all(w in t for w in ("domain", "application", "adapters"))}
    return all(parts.values()), ", ".join(f"{k}={'yes' if v else 'NO'}" for k, v in parts.items())


@check("bootstrap-invoicing", "Facts the user did not give")
def _(ctx):
    rules = ctx.read("docs/business-rules.md") or ctx.docs_text()
    hits = re.findall(r"[^|\n]*(?:\b\d+\s*(?:years?|%)|\bEUR\b|€|\$|£|\bVAT[- ]?(?:number|ID)\b[^|\n]*format)[^|\n]*", rules)
    return None, f"{len(hits)} rule line(s) with a number of years, a percentage or a currency: " + " || ".join(h.strip()[:80] for h in hits[:4])


@check("bootstrap-invoicing", "No rule is restated")
def _(ctx):
    rules_path = ctx.project / "docs/business-rules.md"
    if not rules_path.is_file():
        return None, "no separate business-rules.md"
    norm = lambda s: re.findall(r"[a-z0-9]+", s.lower())
    others = {p.name: " ".join(norm(p.read_text(errors="replace"))) for p in ctx.files("docs/*.md", "CLAUDE.md") if p.name != "business-rules.md"}
    found = []
    for rid, rest in RULE_ROW.findall(rules_path.read_text(errors="replace")):
        words = norm(rest.split("|")[0])
        for i in range(0, max(len(words) - 7, 0)):
            run = " ".join(words[i:i + 8])
            for name, body in others.items():
                if run in body:
                    found.append(f"{rid} in {name}: '{run}'")
                    break
            else:
                continue
            break
    if found:
        return False, f"{len(found)} rule(s) with an 8-word run repeated verbatim: " + "; ".join(found[:3])
    return None, "no verbatim 8-word run repeated; reworded restatement needs reading"


@check("bootstrap-invoicing", "Domain model has a ubiquitous language")
def _(ctx):
    t = ctx.read("docs/domain-model.md")
    lang = re.search(r"ubiquitous language.*?\n(?:.*\n){0,6}?\|.*\|", t, re.I)
    ports = re.search(r"ports.*?\n(?:.*\n){0,6}?\|.*\|", t, re.I)
    return bool(lang and ports), f"language table={bool(lang)}, ports table={bool(ports)}"


@check("bootstrap-invoicing", "The branch guard hook")
def _(ctx):
    return branch_guard(ctx)


def branch_guard(ctx: Ctx):
    hook = ctx.project / ".claude/hooks/block_commit_on_main.py"
    settings = ctx.read(".claude/settings.json")
    if not hook.is_file() or "block_commit_on_main" not in settings:
        return False, f"hook file={hook.is_file()}, referenced in settings.json={'block_commit_on_main' in settings}"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", "-b", "main", tmp], check=True)
        payload = json.dumps({"tool_input": {"command": "git commit -m x"}, "cwd": tmp})
        rc, out = ctx.sh([sys.executable, str(hook)], cwd=Path(tmp), stdin=payload)
    return '"deny"' in out, "hook denies `git commit` on main" if '"deny"' in out else f"hook output: {out[:100]!r}"


# ---- build-book-room ----------------------------------------------------------------------------------

@check("build-book-room", "Work is not done on main")
def _(ctx): return branch_and_commits(ctx)


@check("build-book-room", "Unit tests exist for RM-01")
def _(ctx):
    text = "\n".join(f.read_text(errors="replace") for f in ctx.files("tests/unit/**/*.py"))
    missing = [i for i in ("RM-01", "BK-01", "BK-02", "BK-03", "BK-04", "BK-05") if not re.search(rf"@rule[^\n]*{i}\b", text)]
    return not missing, f"rules without an @rule tag in tests/unit: {missing or 'none'}"


@check("build-book-room", "Unit tests for domain and service code were created before")
def _(ctx):
    return None, "order of creation is in log.md"


@check("build-book-room", "The unit tests pass")
def _(ctx): return run_unit(ctx)


@check("build-book-room", "The domain package imports no web framework")
def _(ctx):
    dirs = ctx.domain_dirs("domain")
    hits = [h for h in grep(py_files(dirs), r"^\s*(import|from)\s+(" + DRIVERS + r")")]
    return not hits, f"{len(hits)} import(s)" + (": " + "; ".join(hits[:3]) if hits else "")


@check("build-book-room", "A BookingRepository port")
def _(ctx):
    port = grep(py_files(ctx.domain_dirs("application")), r"class\s+BookingRepository")
    fake = grep(ctx.files("tests/**/*.py"), r"class\s+(InMemory|Fake)\w*Booking\w*")
    return bool(port and fake), f"port={port[:1]}, fake={fake[:1]}"


@check("build-book-room", "A test covers the boundary where one booking ends")
def _(ctx):
    return None, "tests mentioning touching/adjacent periods: " + "; ".join(grep(ctx.files("tests/unit/**/*.py"), r"touch|adjacent|back.to.back|ends_exactly|starts_when")[:4])


@check("build-book-room", "A test covers a booking of exactly 8 hours")
def _(ctx):
    return None, "tests with an 8-hour period: " + "; ".join(grep(ctx.files("tests/unit/**/*.py"), r"hours\s*=\s*8|timedelta\(hours=8\)|exactly[_ ]eight|8[_ ]hours")[:4])


@check("build-book-room", "The final report lists rule IDs")
def _(ctx): return None, "report content"


@check("build-book-room", "The report states honestly")
def _(ctx): return None, "report content"


@check("build-book-room", "No HTTP route or web framework")
def _(ctx):
    hits = grep(py_files([ctx.project / "src"]), WEB) + grep([ctx.project / "pyproject.toml"] if ctx.has_pyproject else [], WEB)
    return not hits, f"{len(hits)} hit(s)" + (": " + "; ".join(hits[:3]) if hits else "")


@check("build-book-room", "No dependency outside")
def _(ctx):
    old = pyproject_deps(dependency_lists(ctx.head_text("pyproject.toml") or ""))
    new = pyproject_deps(dependency_lists(ctx.read("pyproject.toml")))
    added = sorted(new - old)
    return not added, f"dependencies added to pyproject.toml: {added or 'none'}"


@check("build-book-room", "Documents were changed only")
def _(ctx):
    rc, out = ctx.git("diff", "HEAD", "--stat", "--", "docs")
    return None, "git diff --stat docs: " + out.replace("\n", " | ")[:300]


@check("build-book-room", "The domain layer calls no platform clock")
def _(ctx): return domain_forbidden(ctx, CLOCK)


@check("build-book-room", "A test shows that two overlapping bookings made at the same moment")
def _(ctx):
    tests = ctx.files("tests/integration/**/*.py")
    threads = grep(tests, CONCURRENCY)
    stale = grep(tests, r"concurrent|stale|race|ExclusionViolation|IntegrityError|bookings_no_overlap|hides?\b")
    if not threads and not stale:
        return False, "no concurrency primitive and no stale-read test caught by the constraint"
    return None, f"threaded: {threads[:2] or 'none'}; stale-read or constraint: {stale[:3] or 'none'} (read them)"


@check("build-book-room", "Every test tagged with a rule ID")
def _(ctx):
    tags = tagged_tests(ctx)
    wide = [t for t in tags if len(re.findall(r"[A-Z]{2,5}-\d+", t)) >= 3]
    partial = grep(ctx.files("tests/**/*.py"), r"@rule\s+[A-Z]{2,5}-\d+[^\n]*\(")
    return None, (f"{len(tags)} tag(s); tests tagged with 3+ rules (likely overclaiming): {wide[:4]}; "
                  f"tags marked partial: {partial[:4] or 'none'}")


@check("build-book-room", "No UC-02")
def _(ctx):
    hits = grep(py_files([ctx.project / "src"]), r"class\s+Cancel\w*|def\s+cancel\w*|UC-02")
    return not hits, f"{len(hits)} hit(s) in src" + (": " + "; ".join(hits[:3]) if hits else "")


# ---- review-returns-docs --------------------------------------------------------------------------------

@check("review-returns-docs", "Used the traceability script")
def _(ctx):
    log = ctx.output_text("log.md")
    return ("check_traceability" in log) if log else None, "log.md mentions check_traceability" if "check_traceability" in log else "log.md missing or no mention"


@check("review-returns-docs", "Work happened on a branch")
def _(ctx): return branch_and_commits(ctx)


# ---- change-booking-limits ---------------------------------------------------------------------------------

OLD_VALUES = (r"\b(3|three)\b[^.|\n]{0,30}upcoming|upcoming[^.|\n]{0,30}\b(3|three)\b|\b(8|eight)[ -]hours?\b|hours\s*=\s*8"
              r"|MAX_\w*\s*=\s*3\b|lowered from|changed from|was (3|8)\b|from (3|8) to|\(20\d\d-\d\d-\d\d")


@check("change-booking-limits", "Both rules keep their IDs")
def _(ctx):
    rules = ctx.read("docs/business-rules.md")
    ids = {i: bool(re.search(rf"^\|\s*{i}\s*\|", rules, re.M)) for i in ("BK-01", "BK-04")}
    marked = bool(re.search(r"^\|\s*BK-0[14]\s*\|[^\n]*\((removed|superseded)", rules, re.M))
    hits = grep([p for p in ctx.files("docs/*.md", "src/**/*.py") if p.name != "technical-spec.md"], OLD_VALUES)
    # The Decisions section is where the reason for the change belongs, so it may name the old value.
    spec = re.sub(r"^##\s*Decisions.*?(?=^##\s|\Z)", "", ctx.read("docs/technical-spec.md"), flags=re.M | re.S)
    hits += [f"technical-spec.md: {m.group(0).strip()[:80]}" for m in re.finditer(r"[^\n]*(?:" + OLD_VALUES + r")[^\n]*", spec, re.I)]
    ok = all(ids.values()) and not marked and not hits
    return ok, f"IDs present={ids}; old-value or history-note hits (tests excluded)={len(hits)}" + (": " + "; ".join(hits[:4]) if hits else "")


@check("change-booking-limits", "Tests are moved to the new boundaries")
def _(ctx):
    ok, ev = run_unit(ctx)
    text = "\n".join(f.read_text(errors="replace") for f in ctx.files("tests/**/*.py"))
    tags = all(re.search(rf"@rule[^\n]*{i}\b", text) for i in ("BK-01", "BK-04"))
    return ok and tags, f"unit: {ev}; BK-01 and BK-04 tagged={tags}; boundary values need reading"


@check("change-booking-limits", "The limit values live in one place")
def _(ctx):
    return None, "constants: " + "; ".join(grep(py_files([ctx.project / "src"]), r"^\s*[A-Z_]{4,}\s*=\s*(\d|timedelta)")[:6])


@check("change-booking-limits", "The effect on existing bookings")
def _(ctx): return None, "questions.md content"


@check("change-booking-limits", "Integration tests were run")
def _(ctx): return run_integration(ctx)


@check("change-booking-limits", "A change report")
def _(ctx): return None, "report content"


@check("change-booking-limits", "A stored booking longer")
def _(ctx): return stored_booking_probe(ctx)


@check("change-booking-limits", "The change and its reason are recorded")
def _(ctx):
    now, before = section(ctx.read("docs/technical-spec.md"), "Decisions"), section(ctx.head_text("docs/technical-spec.md") or "", "Decisions")
    return bool(now.strip()) and now.strip() != before.strip(), f"Decisions section changed={now.strip() != before.strip()}, {len(now.split())} words"


@check("change-booking-limits", "The traceability check was run with the ID-stability")
def _(ctx):
    ok, ev = traceability(ctx, history=True)
    return ok, "re-run against HEAD: " + ev


PROBE = '''
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
import pytest

PROJECT = Path(os.environ["PROBE_PROJECT"])
ROOM = uuid.UUID("7c0d3a52-0b1e-4c55-9a52-000000000001")


@pytest.fixture
def conn():
    with psycopg.connect(os.environ["DATABASE_URL"]) as c:
        with c.transaction(force_rollback=True):
            for m in sorted((PROJECT / "migrations").glob("*.sql")):
                c.execute(m.read_text())
            yield c


def test_stored_booking_over_the_new_limit_still_blocks_its_room(conn):
    from roombooking.application.book_room import BookRoomCommand
    from roombooking.bootstrap import book_room
    from roombooking.domain.errors import BookingRejected

    start = datetime.now(UTC).replace(microsecond=0) + timedelta(days=30)
    conn.execute(
        "INSERT INTO bookings (id, room_id, member_id, starts_at, ends_at) VALUES (%s, %s, %s, %s, %s)",
        (uuid.uuid4(), ROOM, uuid.uuid4(), start, start + timedelta(hours=6)),
    )
    with pytest.raises(BookingRejected) as e:
        book_room(conn).execute(BookRoomCommand(uuid.uuid4(), ROOM, start + timedelta(hours=1), start + timedelta(hours=2)))
    assert e.value.code == "room_already_booked"
'''


def stored_booking_probe(ctx: Ctx):
    if "DATABASE_URL" not in ctx.extra_env:
        return None, "not run: pass --env DATABASE_URL=..."
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "test_probe.py"
        probe.write_text(PROBE)
        ctx.env["PROBE_PROJECT"] = str(ctx.project)
        rc, out = ctx.sh(["uv", "run", "pytest", str(probe), "-q", "-p", "no:cacheprovider", "--rootdir", tmp], cwd=ctx.project)
    if rc == 0:
        return True, "a stored 6-hour booking still blocks its room (room_already_booked)"
    if "booking_too_long" in out:
        return False, "a stored 6-hour booking fails with booking_too_long instead of room_already_booked"
    return None, "probe could not run against this project's API: " + (out.splitlines()[-1] if out else "")[:120]


# ---- change-new-use-case --------------------------------------------------------------------------------------

@check("change-new-use-case", "The kinds of change")
def _(ctx): return None, "questions.md and log.md order"


@check("change-new-use-case", "New behaviour is stated as rules")
def _(ctx):
    now, before = rule_ids(ctx.read("docs/business-rules.md")), rule_ids(ctx.head_text("docs/business-rules.md") or "")
    new = sorted(now - before)
    return bool(new) and not (before - now), f"new rule IDs: {new or 'none'}; rule IDs lost: {sorted(before - now) or 'none'}"


@check("change-new-use-case", "UC-03 is added")
def _(ctx):
    now = dict(UC_ROW.findall(ctx.read("docs/use-cases.md")))
    before = dict(UC_ROW.findall(ctx.head_text("docs/use-cases.md") or ""))
    changed = [k for k in before if now.get(k) != before[k]]
    return "UC-03" in now and not changed, f"UC-03 present={'UC-03' in now}; existing rows changed={changed or 'none'}"


@check("change-new-use-case", "Domain model, technical spec and functional spec")
def _(ctx):
    new = sorted(rule_ids(ctx.read("docs/business-rules.md")) - rule_ids(ctx.head_text("docs/business-rules.md") or ""))
    where = {}
    for d in ("domain-model", "technical-spec", "functional-spec"):
        text = ctx.read(f"docs/{d}.md")
        where[d] = [i for i in new if i in text]
    return None, f"new rule IDs cited per document: {where}"


@check("change-new-use-case", "New tests carry")
def _(ctx):
    rc, out = ctx.git("status", "--porcelain", "--untracked-files=all", "--", "tests")
    new_files = [l[3:] for l in out.splitlines() if l.startswith("??") or l.startswith(" M")]
    untagged = [f for f in new_files if f.endswith(".py") and not re.search(r"@(rule|usecase)", ctx.read(f))]
    return None, f"{len(new_files)} new or changed test file(s); without any tag: {untagged or 'none'}; order of writing is in log.md"


@check("change-new-use-case", "No behaviour is invented")
def _(ctx): return None, "questions.md and open points"


@check("change-new-use-case", "Every test tagged with a rule ID")
def _(ctx):
    tags = tagged_tests(ctx)
    wide = [t for t in tags if len(re.findall(r"[A-Z]{2,5}-\d+", t)) >= 3]
    return None, f"{len(tags)} tag(s); tests tagged with 3+ rules: {wide[:4]}; read each new tagged test against its rule"


# ---- change-db-swap -------------------------------------------------------------------------------------------

@check("change-db-swap", "Domain and application layers are unchanged")
def _(ctx):
    paths = [str(d.relative_to(ctx.project)) for layer in ("domain", "application") for d in ctx.domain_dirs(layer)]
    rc, out = ctx.git("status", "--porcelain", "--untracked-files=all", "--", *paths)
    return not out.strip(), f"changed files under {paths}: {out.replace(chr(10), ', ') or 'none'}"


@check("change-db-swap", "The new driver is recorded")
def _(ctx):
    old = pyproject_deps(dependency_lists(ctx.head_text("pyproject.toml") or ""))
    new = pyproject_deps(dependency_lists(ctx.read("pyproject.toml")))
    added = sorted(new - old)
    spec = ctx.read("docs/technical-spec.md").lower()
    stack = section(ctx.read("docs/technical-spec.md"), "Stack").lower()
    unlisted = [d for d in added if d.lower().replace("-", "") not in stack.replace("-", "")]
    q = ctx.output_text("questions.md").lower()
    asked = [d for d in added if d.lower().replace("-", "") in q.replace("-", "")] if q else None
    return (not unlisted and bool(added)) and (asked is None or len(asked) > 0), f"added={added}; missing from stack table={unlisted or 'none'}; named in questions.md={asked}"


@check("change-db-swap", "The BK-02 guarantee that relied")
def _(ctx):
    hits = grep(ctx.files("tests/**/*.py"), CONCURRENCY)
    if not hits:
        return False, "no threading or executor in any test"
    return None, "tests with concurrency primitives: " + "; ".join(hits[:4])


@check("change-db-swap", "A Decisions entry")
def _(ctx):
    now, before = section(ctx.read("docs/technical-spec.md"), "Decisions"), section(ctx.head_text("docs/technical-spec.md") or "", "Decisions")
    changed = now.strip() != before.strip()
    return changed and bool(re.search(r"reject", now, re.I)), f"Decisions changed={changed}, mentions a rejected alternative={bool(re.search('reject', now, re.I))}"


@check("change-db-swap", "The existing migration")
def _(ctx):
    rc, out = ctx.git("status", "--porcelain", "--untracked-files=all", "--", "migrations")
    return None, f"migration changes: {out.replace(chr(10), ', ') or 'none'}; compare with the order in questions.md and log.md"


@check("change-db-swap", "Tests pass against a real MySQL")
def _(ctx): return run_integration(ctx)


@check("change-db-swap", "The BK-02 guarantee covers every write path")
def _(ctx): return mysql_write_paths(ctx)


@check("change-db-swap", "Any claim that MySQL cannot")
def _(ctx):
    spec = ctx.read("docs/technical-spec.md")
    claims = re.findall(r"[^.\n]*(?:cannot|can't|does not support|no support|impossible)[^.\n]*", section(spec, "Decisions"), re.I)
    return None, f"'cannot' claims in Decisions: {[c.strip()[:100] for c in claims[:3]]}"


@check("change-db-swap", "The concurrency test makes both")
def _(ctx):
    locks = grep(ctx.files("migrations/*.sql", "src/**/*.py"), r"FOR UPDATE|FOR SHARE|GET_LOCK|LOCK TABLES|SERIALIZABLE")
    return None, f"{len(locks)} lock statement(s): " + "; ".join(locks[:6]) + "; check by removing one lock in a copy"


def mysql_write_paths(ctx: Ctx):
    if not ctx.mysql_container:
        return None, "not run: pass --mysql-container NAME"
    db = "probe_" + os.urandom(3).hex()
    mysql = ["docker", "exec", "-i", ctx.mysql_container, "mysql", "-uroot", f"-p{ctx.mysql_password}"]
    def run(sql: str, database: str | None = None):
        return ctx.sh(mysql + ([database] if database else []), stdin=sql)
    try:
        run(f"CREATE DATABASE {db}")
        for m in sorted((ctx.project / "migrations").glob("*.sql")):
            rc, out = run(m.read_text(), db)
            if rc != 0:
                return None, f"migration {m.name} did not apply on MySQL: {out[:100]}"
        room = "7c0d3a52-0b1e-4c55-9a52-0000000000aa"
        run(f"INSERT INTO rooms (id, name) VALUES ('{room}', 'probe')", db)
        ins = lambda i, a, b, status="active": (f"INSERT INTO bookings (id, room_id, member_id, starts_at, ends_at, status) VALUES "
                                                f"('7c0d3a52-0b1e-4c55-9a52-00000000{i:04d}', '{room}', '7c0d3a52-0b1e-4c55-9a52-00000000ffff', "
                                                f"'2031-01-01 {a}:00:00', '2031-01-01 {b}:00:00', '{status}')")
        results = {}
        results["insert A (ok)"] = run(ins(1, "10", "12"), db)[0] == 0
        results["overlapping insert rejected"] = run(ins(2, "11", "13"), db)[0] != 0
        results["touching insert ok"] = run(ins(3, "12", "13"), db)[0] == 0
        results["update into overlap rejected"] = run("UPDATE bookings SET starts_at='2031-01-01 11:00:00' WHERE id='7c0d3a52-0b1e-4c55-9a52-000000000003'", db)[0] != 0
        results["cancelled overlap insert ok"] = run(ins(4, "10", "11", "cancelled"), db)[0] == 0
        results["reactivation into overlap rejected"] = run("UPDATE bookings SET status='active' WHERE id='7c0d3a52-0b1e-4c55-9a52-000000000004'", db)[0] != 0
        bad = [k for k, v in results.items() if not v]
        return not bad, "; ".join(f"{k}={'ok' if v else 'FAILED'}" for k, v in results.items())
    finally:
        run(f"DROP DATABASE IF EXISTS {db}")


# ---- adopt-library-loans ----------------------------------------------------------------------------------

def full_suite(ctx: Ctx):
    """Run the whole suite; returns (failed test ids, errors, summary line) or None when not runnable."""
    if "DATABASE_URL" not in ctx.extra_env:
        return None
    rc, out = ctx.tool("suite", ["uv", "run", "pytest", "-q", "-rfE", "-p", "no:cacheprovider"])
    failed = re.findall(r"^FAILED (\S+)", out, re.M)
    errors = re.findall(r"^ERROR (\S+)", out, re.M)
    return failed, errors, out.splitlines()[-1] if out else "no output"


@check("adopt-library-loans", "No file under src/ or migrations/")
@check("adopt-confirmation", "No file under src/ or migrations/")
def _(ctx):
    rc, out = ctx.git("status", "--porcelain", "--untracked-files=all", "--", "src", "migrations")
    rc2, diff = ctx.git("diff", "--stat", "HEAD", "--", "src", "migrations")
    return not out.strip() and not diff.strip(), f"changes: {out.replace(chr(10), ', ') or 'none'}"


@check("adopt-library-loans", "Work is on a new branch")
@check("fix-double-return", "Work is on a new branch")
def _(ctx): return branch_and_commits(ctx)


@check("adopt-library-loans", "The starting state of the test suite")
def _(ctx):
    test = ctx.read("tests/test_fees.py")
    m = re.search(r"((?:^@.*\n)*)def test_fee_is_capped\(\):\n(.*?)(?=^def |\Z)", test, re.M | re.S)
    if not m:
        return False, "test_fee_is_capped is gone from tests/test_fees.py"
    intact = "== 15.0" in m.group(2) and not re.search(r"skip|xfail", m.group(1) + m.group(2))
    if not intact:
        return False, f"test_fee_is_capped was changed: {(m.group(1) + m.group(2)).strip()[:120]}"
    docs = ctx.docs_text()
    mentioned = "test_fee_is_capped" in docs
    return (True if mentioned else None), f"test intact; named in docs={mentioned} (else look for the starting state in the report)"


@check("adopt-library-loans", "docs/adoption.md maps")
def _(ctx):
    text = ctx.read("docs/adoption.md")
    if not text:
        return False, "docs/adoption.md missing"
    areas = {a: bool(re.search(a, text, re.I)) for a in ("loan", "member", "catalog|book")}
    return None, f"areas named: {areas}; statuses: {sorted(set(re.findall(r'not adopted|in progress|adopted', text, re.I)))}"


@check("adopt-library-loans", "business-rules.md holds the loan rules")
def _(ctx):
    rules = ctx.read("docs/business-rules.md")
    if not rules:
        return False, "docs/business-rules.md missing"
    rows = RULE_ROW.findall(rules)
    other = [f"{i}: {r.strip()[:60]}" for i, r in rows if re.search(r"e-?mail|isbn|payment|pay_fees|\bpays?\b", r, re.I)]
    return None, f"{len(rows)} rule rows; rows touching other areas: {other or 'none'}"


@check("adopt-library-loans", "The two rules that exist only in the schema")
def _(ctx):
    rows = " ".join(r for _, r in RULE_ROW.findall(ctx.read("docs/business-rules.md")))
    one = bool(re.search(r"one (open|active|current)|single (open|active)|already (on loan|lent|out)|at a time", rows, re.I))
    ren = bool(re.search(r"renew\w*[^|]*\b(2|two)\b|\b(2|two)\b[^|]*renew", rows, re.I))
    return (True if one and ren else None), f"one-open-loan rule found={one}; max-2-renewals rule found={ren}"


@check("adopt-library-loans", "The conflicting loan limits")
def _(ctx):
    text = ctx.docs_text() + ctx.output_text("questions.md")
    hits = grep([p for p in ctx.files("docs/*.md")], r"web\.py.*\b5\b|\b5\b.*web\.py|MAX_LOANS\s*=\s*5|\b3\b.*\b5\b|\b5\b.*\b3\b")
    q = bool(re.search(r"\b5\b", ctx.output_text("questions.md")))
    return None, f"doc lines naming both limits: {hits[:3]}; questions.md mentions 5={q}"


@check("adopt-library-loans", "Late fees computed on floats")
def _(ctx):
    hits = grep(ctx.files("docs/*.md"), r"float|decimal|rounding")
    return None, f"doc lines on float/decimal: {hits[:3]}"


@check("adopt-library-loans", "Each loan rule names where it is enforced")
def _(ctx):
    refs = grep(ctx.files("docs/*.md"), r"\b[\w/]+\.(py|sql):\d+")
    return None, f"{len(refs)} file:line reference(s) in docs, e.g. {refs[:3]}"


@check("adopt-library-loans", "Existing tests that cover a rule")
def _(ctx):
    tagged = bool(re.search(r"@rule\s+[A-Z]{2,5}-\d", ctx.read("tests/test_fees.py")))
    dupes = [h for h in grep(ctx.files("tests/**/*.py"), r"late_fee\(") if not h.startswith("test_fees.py")]
    return (True if tagged and not dupes else None), f"test_fees.py tagged={tagged}; late_fee tests elsewhere: {dupes[:3] or 'none'}"


@check("adopt-library-loans", "Every loan rule has a test")
def _(ctx):
    ok, ev = traceability(ctx, history=False)
    if not ok:
        return False, ev
    out = ctx._cache.get("trace-False", (1, ""))[1]
    untested = [l for l in out.splitlines() if "has no test" in l]
    return (True if not untested else None), ev + f"; rules without a test: {len(untested)} (compare with the 'not testable' list)"


@check("adopt-library-loans", "Tests other than test_fee_is_capped pass")
@check("fix-double-return", "Tests other than test_fee_is_capped pass")
def _(ctx):
    res = full_suite(ctx)
    if res is None:
        return None, "not run: pass --env DATABASE_URL=..."
    failed, errors, last = res
    others = [f for f in failed if "test_fee_is_capped" not in f]
    if errors and not others:
        return None, f"{len(errors)} error(s) at setup ({last}); check the project's database convention"
    new_db_tests = grep(ctx.files("tests/**/*.py"), r"DATABASE_URL|connect\(|psycopg")
    return not others and not errors and bool(new_db_tests), f"{last}; other failures: {others or 'none'}; tests using the database: {len(new_db_tests)}"


@check("adopt-library-loans", "An architecture check is configured")
def _(ctx):
    py = ctx.read("pyproject.toml")
    if "importlinter" in py:
        rc, out = ctx.tool("lint-imports", ["uv", "run", "lint-imports"])
        ignores = len(re.findall(r'"[\w.]+ -> [\w.]+"', py))
        return None, f"lint-imports exit {rc}: {out.splitlines()[-1][:80] if out else ''}; ignore_imports entries: {ignores}"
    base = ctx.files("**/*baseline*")
    return None, f"no import-linter config; baseline-like files: {[str(b.relative_to(ctx.project)) for b in base][:3]}"


@check("adopt-library-loans", "Adding a new dev tool")
def _(ctx):
    old = pyproject_deps(dependency_lists(ctx.head_text("pyproject.toml") or ""))
    new = pyproject_deps(dependency_lists(ctx.read("pyproject.toml")))
    added = sorted(new - old)
    if not added:
        return True, "no dependency added"
    q = ctx.output_text("questions.md").lower()
    asked = [d for d in added if d.lower() in q]
    return (len(asked) == len(added)) if q else None, f"added={added}; named in questions.md={asked}"


def question_sections(ctx: Ctx) -> list[tuple[str, str]]:
    """(heading, body) of each '## ' section of outputs/questions.md, in order."""
    text = ctx.output_text("questions.md")
    parts = re.split(r"^##\s+(.*)$", text, flags=re.M)
    return list(zip(parts[1::2], parts[2::2]))


CHOICE = re.compile(r"\bor\b|\?|\bvs\.?\b|\bversus\b", re.I)


@check("adopt-library-loans", "There is one recap, right before")
@check("adopt-confirmation", "There is one recap, right before")
def recap_form(ctx):
    """The recap is found by position, not by its title: the shown (non-question) sections between the
    choice of area and the batch of settled candidates. Exactly one is expected, directly before the batch."""
    secs = question_sections(ctx)
    if not secs:
        return False, "no outputs/questions.md sections"
    heads = [h for h, _ in secs]
    is_question = lambda h: bool(re.match(r"(Q|Questions?)\s*\d|\d+\.\s", h)) and not re.search(r"shown|recap|summary", h, re.I)
    batch = next((i for i, h in enumerate(heads) if re.search(r"settled|integrity", h, re.I) and is_question(h)), None)
    if batch is None:
        return False, "no batch of settled candidates, so no confirmation start to find a recap before"
    area = max((i for i, h in enumerate(heads[:batch]) if re.search(r"first area|which area|area", h, re.I) and is_question(h)), default=-1)
    shown = [i for i in range(area + 1, batch) if not is_question(heads[i])]
    if len(shown) != 1 or shown[0] != batch - 1:
        return False, f"shown sections between area choice and batch: {[heads[i][:45] for i in shown]}"
    body = secs[batch - 1][1]
    tail = re.split(r"matter most|most important|key decisions|decisions that matter|decisions? (you|to) (make|take)", body, flags=re.I)
    items = re.findall(r"^\s*\d+\.\s+(.*)$", tail[-1] if len(tail) > 1 else body, re.M)
    choices = [it for it in items if CHOICE.search(it)]
    ratio = len(choices) / len(items) if items else 0
    return len(items) >= 3 and ratio >= 0.75, f"recap '{heads[batch - 1][:45]}'; {len(choices)}/{len(items)} top decisions written as choices"


@check("adopt-library-loans", "Settled candidates are confirmed in one batch")
@check("adopt-confirmation", "Settled candidates are confirmed in one batch")
def _(ctx):
    heads = [h for h, _ in question_sections(ctx)]
    last_recap = max((i for i, h in enumerate(heads) if re.search(r"recap|summary", h, re.I)), default=-1)
    batch = [h for h in heads[last_recap + 1:] if re.search(r"settled|integrity|one batch", h, re.I)]
    return (None if batch else False), f"batch section: {batch[:1] or 'none'}; headings after it: {heads[heads.index(batch[0]) + 1:][:6] if batch else []}"


@check("adopt-confirmation", "For the rules only the database enforces")
def _(ctx):
    q = ctx.output_text("questions.md")
    asked = bool(re.search(r"(in|by) the domain[^.\n]*(as well|too|also)|database alone|only the database", q, re.I))
    return (True if asked else None), f"domain-enforcement option found in questions.md={asked}"


@check("adopt-library-loans", "An adoption report in the skill's format opens")
def _(ctx): return None, "report content"


# ---- fix-double-return ------------------------------------------------------------------------------------

def rule_row(text: str, rid: str) -> str:
    m = re.search(rf"^\|\s*{rid}\s*\|.*$", text, re.M)
    return m.group(0) if m else ""


@check("fix-double-return", "The work is treated as a fix of LN-12")
def _(ctx):
    same = rule_row(ctx.head_text("docs/business-rules.md") or "", "LN-12") == rule_row(ctx.read("docs/business-rules.md"), "LN-12")
    return (None if same else False), f"LN-12 row unchanged={same}; read the report for the Fix/Change decision"


@check("fix-double-return", "The expected-failure marker")
def _(ctx):
    text = ctx.read("tests/integration/test_lending.py")
    m = re.search(r"((?:^@.*\n|^    .*\n|^\)\n)*)def test_returned_loan_cannot_be_returned_again", text, re.M)
    if not m:
        return False, "test_returned_loan_cannot_be_returned_again is gone"
    marked = "xfail" in m.group(1)
    tests = re.findall(r"def (test_\w+)\([^)]*\):\n\s+\"\"\"[^\n]*LN-12", ctx.read("tests/integration/test_lending.py"))
    others = [h for h in grep(ctx.files("tests/**/*.py"), r"LN-12") if not h.startswith("test_lending.py")]
    if marked:
        return False, "xfail still on test_returned_loan_cannot_be_returned_again"
    return None, f"marker removed; tests citing LN-12: {tests}; elsewhere: {others or 'none'} (judge whether any repeats the same case)"


@check("fix-double-return", "The test was seen failing")
def _(ctx): return None, "order in log.md"


@check("fix-double-return", "Members already charged twice")
def _(ctx):
    rc, out = ctx.git("status", "--porcelain", "--untracked-files=all", "--", "migrations")
    if out.strip():
        return False, f"migrations changed: {out}"
    q = ctx.output_text("questions.md")
    return None, f"migrations unchanged; questions.md has SELECT={bool(re.search(r'SELECT', q, re.I))}"


@check("fix-double-return", "Only loans.py and web.py changed")
def _(ctx):
    rc, changed = ctx.git("diff", "--name-only", "HEAD", "--", "src")
    rc2, added = ctx.git("ls-files", "--others", "--exclude-standard", "--", "src")
    files = [f for f in (changed + "\n" + added).splitlines() if f.strip()]
    other = [f for f in files if f not in ("src/library/loans.py", "src/library/web.py")]
    return not other and bool(files), f"changed under src: {files or 'none'}"


@check("fix-double-return", "The LN-12 open point is closed")
def _(ctx):
    spec = ctx.read("docs/functional-spec.md")
    line = next((l for l in spec.splitlines() if "LN-12" in l and re.search(r"code differs|open point", l, re.I)), "")
    open_still = line.strip().startswith("- [ ]")
    enf = rule_row(ctx.read("docs/technical-spec.md"), "LN-12")
    return (None if not open_still else False), f"open point line: {line.strip()[:90] or 'gone'}; enforcement: {enf[:120]}"


LINE_REF = re.compile(r"[\w./-]+\.(?:py|sql|ts|php|java|kt)(?::\d+(?:[-,]\d+)*)+\b")


@check("fix-double-return", "Document lines the fix added or changed cite the code it changed")
def _(ctx):
    rc, diff = ctx.git("diff", "-U0", "HEAD", "--", "docs")
    rc2, changed = ctx.git("diff", "--name-only", "HEAD", "--", "src", "migrations")
    changed_files = {c.strip() for c in changed.splitlines() if c.strip()}
    added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    with_lines = [m.group(0) for l in added for m in LINE_REF.finditer(l) if m.group(0).split(":")[0] in changed_files]
    row = rule_row(ctx.read("docs/technical-spec.md"), "LN-12")
    row_ok = "::" in row and not LINE_REF.search(row)
    return (not with_lines and row_ok), f"line references to changed code in added doc lines: {with_lines[:4] or 'none'}; LN-12 row: {row[:110]}"


@check("fix-double-return", "The architecture check and the traceability check pass")
def _(ctx):
    rc, out = ctx.tool("lint-imports", ["uv", "run", "lint-imports"])
    ok, ev = traceability(ctx)
    return rc == 0 and ok, f"lint-imports exit {rc}; traceability {ev}"


@check("fix-double-return", "A fix report")
def _(ctx):
    rep = ctx.output_text("report.md").lstrip("`\n ")
    return (True if rep.startswith("Fix:") else None), f"report starts with: {rep[:60]!r}"


# ---- progress plan ----------------------------------------------------------------------------------------

def plan_lines(ctx: Ctx, pattern: str) -> list[str]:
    return [l.strip() for l in ctx.read("docs/plan.md").splitlines() if re.search(pattern, l)]


def now_clear(ctx: Ctx) -> bool:
    now = section(ctx.read("docs/plan.md"), "Now")
    return not re.search(r"^\s*- \[ \]", now, re.M)


@check("build-book-room", "docs/plan.md was created from the documents")
def _(ctx):
    if not (ctx.project / "docs/plan.md").is_file():
        return False, "docs/plan.md missing"
    uc1, uc2 = plan_lines(ctx, r"\bUC-01\b"), plan_lines(ctx, r"\bUC-02\b")
    ok = any(l.startswith("- [x]") for l in uc1) and bool(uc2) and all(l.startswith("- [ ]") for l in uc2)
    return ok, f"UC-01: {uc1[:1]}; UC-02: {uc2[:1]}; Now clear={now_clear(ctx)}"


@check("fix-double-return", "In docs/plan.md the LN-12 fix is ticked")
def _(ctx):
    fixes = [l for l in plan_lines(ctx, r"\bLN-12\b")]
    ticked = [l for l in fixes if l.startswith("- [x]") and re.search(r"\d{4}-\d{2}-\d{2}", l)]
    before = len(re.findall(r"^- \[", section(ctx.head_text("docs/plan.md") or "", "Follow-ups"), re.M))
    after = len(re.findall(r"^- \[", section(ctx.read("docs/plan.md"), "Follow-ups"), re.M))
    ok = bool(ticked) and now_clear(ctx)
    return (ok if not ok else None), f"LN-12 lines: {fixes[:2]}; Now clear={now_clear(ctx)}; follow-ups {before} -> {after} (judge against the report)"


@check("build-book-room", "The run kept a session task list")
@check("fix-double-return", "The run kept a session task list")
def _(ctx): return None, "log.md [task list] lines or transcript"


# ---- driver ------------------------------------------------------------------------------------------------

def tools_report(ctx: Ctx) -> dict:
    report: dict[str, str] = {}
    if ctx.has_pyproject:
        if (ctx.project / "tests" / "unit").is_dir():
            report["unit"] = run_unit(ctx)[1]
        if "DATABASE_URL" in ctx.extra_env and (ctx.project / "tests" / "integration").is_dir():
            report["integration"] = run_integration(ctx)[1]
        for name, cmd in (("mypy", ["uv", "run", "mypy"]), ("ruff", ["uv", "run", "ruff", "check", "."]),
                          ("lint-imports", ["uv", "run", "lint-imports"])):
            rc, out = ctx.tool(name, cmd)
            report[name] = f"exit {rc}: {out.splitlines()[-1][:100] if out else ''}"
    if (ctx.project / "docs/business-rules.md").is_file() or ctx.files("docs/*.md"):
        report["traceability"] = traceability(ctx, history=ctx.eval_name != "bootstrap-invoicing")[1]
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eval_name", choices=sorted(COMMITS_AT_START))
    ap.add_argument("project", type=Path)
    ap.add_argument("--outputs", type=Path)
    ap.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--mysql-container")
    ap.add_argument("--mysql-password", default="test")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    env = dict(kv.split("=", 1) for kv in a.env)
    ctx = Ctx(a.eval_name, a.project.resolve(), a.outputs, env, a.mysql_container, a.mysql_password)

    assertions = next(e for e in json.loads((EVALS / "evals.json").read_text())["evals"] if e["name"] == a.eval_name)["assertions"]
    decided, judgment, used = [], [], set()
    for key, fn in CHECKS.get(a.eval_name, []):
        matches = [t for t in assertions if t.startswith(key)]
        if len(matches) != 1:
            print(f"error: check key {key!r} matches {len(matches)} assertions of {a.eval_name}; update grade_mechanical.py", file=sys.stderr)
            return 2
        text = matches[0]
        used.add(text)
        try:
            passed, evidence = fn(ctx)
        except Exception as e:  # a failing probe must not hide the other checks
            passed, evidence = None, f"check crashed: {type(e).__name__}: {e}"
        (decided if passed is not None else judgment).append({"text": text, "passed": passed, "evidence": evidence})
    judgment += [{"text": t, "passed": None, "evidence": "no mechanical check"} for t in assertions if t not in used]

    result = {"eval": a.eval_name, "project": str(ctx.project), "decided": decided,
              "needs_judgment": judgment, "tools": tools_report(ctx),
              "summary": {"decided": len(decided), "passed": sum(1 for d in decided if d["passed"]), "needs_judgment": len(judgment)}}
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if a.out:
        a.out.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
