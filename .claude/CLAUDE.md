# ddd-hexagonal plugin

This repository is a Claude Code plugin and its own marketplace (`ev-coding`). The plugin root is the repository root, so keep this file in `.claude/`: a `CLAUDE.md` at the root makes `claude plugin validate` warn.

## Layout

- `skills/ddd-hexagonal/`: the skill. All workflow lives in `SKILL.md` and `references/`.
- `commands/`: one thin command per mode. A command only picks the mode, checks the project state and passes `$ARGUMENTS`; never copy workflow steps into it.
- Commands refer to the skill's files through `${CLAUDE_PLUGIN_ROOT}` (`${CLAUDE_PLUGIN_ROOT}/skills/ddd-hexagonal/SKILL.md`, `.../references/`), never as "the ddd-hexagonal skill": another installed copy of the skill (for example in `~/.claude/skills/`) would otherwise be read instead of the plugin's.
- `.claude-plugin/plugin.json`: manifest, the only home of `version`.
- `.claude-plugin/marketplace.json`: catalog with one entry, `"source": "./"`. Never set `version` here.

## Checks

- `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json` after every change to a manifest, command or skill frontmatter.
- Try changes in a scratch project with `claude --plugin-dir <this repo>`.
- Python scripts run with uv (`uv run`), never pip or venv.
- Keep the `SKILL.md` description under 1024 characters (Agent Skills limit).

## Evals

Evals live in `skills/ddd-hexagonal/evals/` (`README.md` has the details). They cost mostly agent tokens, so:

- Make each run's project with `evals/setup_fixture.py`, one folder per run laid out as `<iteration>/eval-<name>/<with_skill|old_skill>/run-1/`, with `outputs/` beside the project.
- Grade with code first: `uv run evals/run_grading.py <iteration> --db-suffix <s> --pg-url ... --mysql-url ...` writes `mechanical.json` into every run. Give a grader agent that file and have it grade only `needs_judgment`; never ask an agent to re-run tests, greps or git comparisons the script already did.
- Keep the 0.3.0 baseline projects and re-grade them with the script when assertions change; do not re-run the baseline for that.
- Run only the evals a change affects (change guidance: the three change evals; review guidance: review-returns-docs; interview or templates: bootstrap-invoicing). The full set, including bootstrap and db-swap, is for before a release.
- When an assertion in `evals.json` is reworded, update its check in `grade_mechanical.py`; the script stops with an error naming it.
- Runs are single samples: the same eval has flipped between iterations. Treat differences of one or two assertions as noise.

## Release

1. Bump `version` in `.claude-plugin/plugin.json` (semver: patch for fixes, minor for new modes or checks).
2. Commit on a branch, merge to `main`.
3. On `main`, run `claude plugin tag --push`. It checks the versions agree and creates `ddd-hexagonal--v<version>`.

Users installed from git get an update only when `version` changes; commits without a bump never reach them.

## Do not

- Ship hooks in the plugin. The branch guard in `skills/ddd-hexagonal/assets/hooks/` is installed per project during Bootstrap, so it only applies where the workflow is used.
- Rename the plugin or the marketplace without a `renames` entry in `marketplace.json`; it breaks existing installs.
