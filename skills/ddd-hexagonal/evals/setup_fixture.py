#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Create an eval project from a fixture: a git repository on main, as Bootstrap would leave it.

Usage:
    uv run setup_fixture.py <fixture> <dest>

Fixtures:
    room-booking        documents and scaffold, no use case implemented (eval build-book-room)
    room-booking-uc01   room-booking plus UC-01 implemented, as a second commit (change evals)
    returns-review      documents with planted contradictions, gaps and duplication (eval review-returns-docs)
    library-legacy      working Flask + PostgreSQL app with no documents, rules scattered (evals adopt-*)
    library-legacy-adopted  library-legacy after Adopt of the Lending area, as a second commit (eval fix-double-return)

The skill's current scripts are copied into tools/ and the branch guard is installed in
.claude/, so a fixture never carries stale copies of them. library-legacy gets neither: it
stands for a project that has never seen the workflow, and installing them is part of Adopt;
library-legacy-adopted gets them with its adoption commit.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
SKILL = EVALS.parent
FIXTURES = EVALS / "fixtures"
LAYERS = {
    "room-booking": ["room-booking"],
    "room-booking-uc01": ["room-booking", "room-booking-uc01"],
    "returns-review": ["returns-review"],
    "library-legacy": ["library-legacy"],
    "library-legacy-adopted": ["library-legacy", "library-legacy-adopted"],
}
WITHOUT_TOOLS = {"library-legacy"}
MESSAGES = {
    "room-booking": "Bootstrap documents and project scaffold",
    "room-booking-uc01": "Implement UC-01 Book a room",
    "returns-review": "Returns desk documents",
    "library-legacy": "Lending desk 0.3.2",
    "library-legacy-adopted": "Adopt the Lending area",
}
IGNORE = shutil.ignore_patterns(".venv", "__pycache__", "*_cache", ".pytest_cache")


def git(dest: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)


def install_tools(dest: Path) -> None:
    tools = dest / "tools"
    tools.mkdir(exist_ok=True)
    for script in ("check_traceability.py", "check_imports.py", "rule_impact.py"):
        shutil.copy2(SKILL / "scripts" / script, tools / script)
    hooks = dest / ".claude" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL / "assets" / "hooks" / "block_commit_on_main.py", hooks)
    shutil.copy2(SKILL / "assets" / "hooks" / "settings.snippet.json", dest / ".claude" / "settings.json")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in LAYERS:
        print(__doc__)
        return 2
    name, dest = sys.argv[1], Path(sys.argv[2])
    if dest.exists() and any(dest.iterdir()):
        print(f"error: {dest} exists and is not empty")
        return 1
    dest.mkdir(parents=True, exist_ok=True)
    git(dest, "init", "-q", "-b", "main")
    git(dest, "config", "user.name", "Eval Fixture")
    git(dest, "config", "user.email", "fixture@example.test")
    installed = False  # tools go in with the first layer that is not a never-adopted project
    for layer in LAYERS[name]:
        shutil.copytree(FIXTURES / layer, dest, dirs_exist_ok=True, ignore=IGNORE)
        if not installed and layer not in WITHOUT_TOOLS:
            install_tools(dest)
            installed = True
        git(dest, "add", "-A")
        git(dest, "commit", "-q", "-m", MESSAGES[layer])
    print(json.dumps({"fixture": name, "path": str(dest.resolve()), "branch": "main"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
