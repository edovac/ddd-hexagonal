# ddd-hexagonal

A Claude Code plugin (one skill) for spec-driven development with Domain-Driven Design and hexagonal architecture, in any language.

It has seven modes. Claude picks one from the request, or you start one with a command:

| Mode | Command | What it does |
| --- | --- | --- |
| **Bootstrap** | `/ddd-hexagonal:bootstrap [description]` | Interview the user and write the document set (functional spec, business rules with IDs, use cases, domain model, technical spec, `CLAUDE.md`) |
| **Adopt** | `/ddd-hexagonal:adopt [area]` | Bring existing code under the workflow, one area at a time: map the codebase, list the rules the code enforces with file:line evidence, confirm them with the user, tag or add tests that pin today's behaviour, and turn on the architecture check with a baseline of known violations. Production code is not changed |
| **Build** | `/ddd-hexagonal:build <use case>` | Implement one use case: branch check, test first for domain code, integration tests on the real database, architecture check, verification against rule IDs, end-of-task report |
| **Change** | `/ddd-hexagonal:change <what changes>` | Add, alter or remove a rule, use case or technology, or rename a concept: impact analysis, then documents, tests, code |
| **Fix** | `/ddd-hexagonal:fix <bug or rule ID>` | Fix a bug against a documented rule: check a rule covers it (otherwise it is a Change), reproduce with a failing `@rule` test, ask about affected data, make the smallest change where the rule lives, close the open point |
| **Review** | `/ddd-hexagonal:review [focus]` | Check documents for contradictions, gaps and duplication, and rules for missing tests |
| **Code review** | `/ddd-hexagonal:code-review [target] [--full] [--fix] [level]` | Review a diff, branch, PR or path against the architecture, rule-ID traceability, the documents, tests and the stack. `--full` runs the built-in `/code-review` first; `--fix` applies the unambiguous fixes |

The commands need the plugin install. A plain skill install still has all seven modes, picked automatically.

## Install

As a plugin (this repository is also its own marketplace):

```
/plugin marketplace add edovac/ddd-hexagonal
/plugin install ddd-hexagonal@ev-coding
```

The full URL `https://github.com/edovac/ddd-hexagonal.git` or a local path also works with `marketplace add`.

To try it without installing, clone the repository and run `claude --plugin-dir <path-to-clone>`:

```
git clone https://github.com/edovac/ddd-hexagonal.git
claude --plugin-dir ./ddd-hexagonal
```

As a plain skill: clone the repository and copy `skills/ddd-hexagonal/` to `~/.claude/skills/ddd-hexagonal/` (personal, all projects) or `<project>/.claude/skills/ddd-hexagonal/` (one project).

The branch guard hook is not enabled by the plugin. The skill installs it into each project during Bootstrap, so it only applies where the workflow is in use.

## Contents

| Path | Purpose |
| --- | --- |
| `.claude-plugin/` | Plugin manifest and single-plugin marketplace |
| `commands/` | One command per mode; each starts the skill in that mode |
| `skills/ddd-hexagonal/SKILL.md` | Workflow, modes and non-negotiable practices |
| `skills/ddd-hexagonal/references/` | Architecture rules, logging policy, interview, Bootstrap tool setup, adopting existing code, change procedures, bug fixes, progress tracking, documentation review, code review, one file per language (PHP, TypeScript, Python with uv, Java/Kotlin) |
| `skills/ddd-hexagonal/assets/templates/` | Templates for the document set (including the progress plan), `CLAUDE.md` and the adoption working file |
| `skills/ddd-hexagonal/assets/hooks/` | Branch guard hook that blocks `git commit` on `main`/`master`, and the settings snippet that enables it |
| `skills/ddd-hexagonal/scripts/check_traceability.py` | Checks rule IDs, use cases and test citations |
| `skills/ddd-hexagonal/scripts/check_imports.py` | Fallback architecture check for languages without a tool, with a baseline for existing code |
| `skills/ddd-hexagonal/scripts/rule_impact.py` | Lists every mention of a rule or use case ID in docs, tests and code, for impact analysis |
| `skills/ddd-hexagonal/evals/` | Test prompts and assertions (`evals.json`), fixture projects and the script that sets one up |

## Adding a language

Follow `skills/ddd-hexagonal/references/new-language.md`. Configuration snippets in the language files are starting points; all four (PHP with Deptrac, TypeScript with dependency-cruiser, Python with uv and import-linter, Java with ArchUnit) were run in Docker against planted violations, and so were their baseline setups for existing code (Adopt). Kotlin shares the Java setup but was not run separately.
