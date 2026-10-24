# Bootstrap: project tools and branch guard

Step 4 of Bootstrap. It makes the project self-contained, so CI and people without the skill can run the checks.

## Scripts

1. Copy `scripts/check_traceability.py`, `scripts/check_imports.py` and `scripts/rule_impact.py` into the project's `tools/` folder. Copy them unchanged, so the review can tell a stale copy from a current one (`references/doc-review.md`).
2. Pick the runner. The scripts need Python 3.10 or later and no packages; each declares this in a PEP 723 header. If `uv --version` works, write commands as `uv run tools/<script>.py`, because uv then finds or downloads a suitable Python. Otherwise check `python3 --version` and write `python3 tools/<script>.py`; below 3.10, tell the user and ask whether to install uv. Use the same runner in `CLAUDE.md` and CI.

## Branch guard

1. Copy `assets/hooks/block_commit_on_main.py` to `.claude/hooks/`.
2. Merge `assets/hooks/settings.snippet.json` into `.claude/settings.json`. Read the file first and merge the `PreToolUse` array; never replace existing settings. If a hook on `Bash` already exists, ask whether to add this one alongside.
3. Tell the user:
   - It refuses `git commit` while the branch is `main` or `master`.
   - It needs `/hooks` opened once, or a restart, if `.claude/` did not exist when the session began.
   - It only guards Claude; a git `pre-commit` hook is the option for guarding people too.

## CLAUDE.md

Create `CLAUDE.md` from `assets/templates/claude-md.template.md`, with the commands filled from the language reference and the script commands using the runner picked above.
