#!/usr/bin/env python3
"""PreToolUse hook: refuse `git commit` while the checked-out branch is main or master.

Reads the hook payload from stdin. Prints a deny decision when a commit is attempted on a
protected branch; prints nothing (allow) in every other case, including when the branch
cannot be determined, so the hook never blocks unrelated work.
"""
import json
import os
import re
import subprocess
import sys

PROTECTED = {"main", "master"}
# `git commit`, `git -C dir commit`, `git -c k=v commit`, chained after && ; | etc.
COMMIT = re.compile(r"(^|[;&|(]\s*|\s)git(\s+(-C\s+\S+|-c\s+\S+|--[\w-]+(=\S+)?))*\s+commit\b")


CD = re.compile(r"(?:^|[;&|(]\s*)cd\s+(\"[^\"]+\"|'[^']+'|[^\s;&|]+)\s*(?:&&|;)")
DASH_C = re.compile(r"git\s+(?:[^;&|]*?\s)?-C\s+(\"[^\"]+\"|'[^']+'|\S+)")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (payload.get("tool_input") or {}).get("command", "") or ""
    match = COMMIT.search(command)
    if match is None:
        return 0
    cwd = payload.get("cwd") or None
    commit_at = match.end(1)  # index of the `git` word
    cds = CD.findall(command[:commit_at])
    if cds:  # `cd <dir> && git commit` acts on <dir>
        target = cds[-1].strip("\"'")
        cwd = target if os.path.isabs(target) or not cwd else os.path.join(cwd, target)
    dash_c = DASH_C.search(command)
    if dash_c:  # `git -C <dir> commit` acts on <dir>, not on the session's directory
        target = dash_c.group(1).strip("\"'")
        cwd = target if os.path.isabs(target) or not cwd else os.path.join(cwd, target)
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=cwd, capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 0
    if branch in PROTECTED:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Commits on '{branch}' are blocked. Propose a new branch name, ask the user, "
                    "create the branch, then commit there."
                ),
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
