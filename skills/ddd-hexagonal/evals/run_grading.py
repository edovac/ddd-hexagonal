#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Run grade_mechanical.py on every run of an eval iteration and write mechanical.json beside each.

Usage:
    uv run run_grading.py <iteration-dir> [--db-suffix _i2]
        [--pg-url 'postgresql://postgres:test@localhost:5433/{db}'] [--pg-container NAME]
        [--mysql-url 'mysql://root:test@127.0.0.1:3306/{db}'] [--mysql-container NAME]
        [--only EVAL ...]

<iteration-dir> holds eval-<name>/<configuration>/run-<n>/ folders, each with an outputs/ folder
and the project the run worked in (the one subfolder with a .git). Every run gets its own database,
named <eval>_<configuration><db-suffix> with dashes as underscores (MySQL: with _test appended,
because the projects refuse other names). With --pg-container the PostgreSQL databases are created
first. Without --pg-url or --mysql-url, the runs that need a database are graded without
integration tests and the probes that use one, and say so.

Writes <run>/mechanical.json and <iteration-dir>/mechanical-summary.json, and prints one line per
run. Hand each mechanical.json to the grader agent and tell it to grade only `needs_judgment`.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POSTGRES = {"build-book-room", "change-booking-limits", "change-new-use-case", "adopt-library-loans"}
MYSQL = {"change-db-swap"}


def find_project(run: Path) -> Path | None:
    for child in sorted(run.iterdir()):
        if child.is_dir() and (child / ".git").exists():
            return child
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iteration", type=Path)
    ap.add_argument("--db-suffix", default="")
    ap.add_argument("--pg-url")
    ap.add_argument("--pg-container")
    ap.add_argument("--mysql-url")
    ap.add_argument("--mysql-container")
    ap.add_argument("--mysql-password", default="test")
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()

    summary, rc = [], 0
    for run in sorted(a.iteration.glob("eval-*/*/run-*")):
        eval_name, config = run.parts[-3][len("eval-"):], run.parts[-2]
        if a.only and eval_name not in a.only:
            continue
        project = find_project(run)
        if project is None:
            print(f"skip {eval_name}/{config}: no project folder with .git in {run}")
            continue
        db = f"{eval_name.replace('-', '_')}_{config}{a.db_suffix}"
        cmd = [sys.executable, str(HERE / "grade_mechanical.py"), eval_name, str(project),
               "--outputs", str(run / "outputs"), "--out", str(run / "mechanical.json")]
        note = ""
        if eval_name in POSTGRES and a.pg_url:
            if a.pg_container:
                subprocess.run(["docker", "exec", a.pg_container, "psql", "-U", "postgres", "-qc", f"CREATE DATABASE {db}"],
                               capture_output=True)  # exists already on a re-run
            cmd += ["--env", f"DATABASE_URL={a.pg_url.format(db=db)}"]
        elif eval_name in MYSQL and a.mysql_url:
            cmd += ["--env", f"DATABASE_URL={a.mysql_url.format(db=db + '_test')}"]
            if a.mysql_container:
                cmd += ["--mysql-container", a.mysql_container, "--mysql-password", a.mysql_password]
        elif eval_name in POSTGRES | MYSQL:
            note = " (no database URL given: integration tests and probes not run)"
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"FAILED {eval_name}/{config}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}")
            rc = 1
            continue
        result = json.loads(r.stdout)
        s = result["summary"]
        print(f"{eval_name:24} {config:11} decided {s['decided']:2} (passed {s['passed']:2})  needs judgment {s['needs_judgment']:2}{note}")
        summary.append({"eval": eval_name, "configuration": config, "run": run.name, **s})
    (a.iteration / "mechanical-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
