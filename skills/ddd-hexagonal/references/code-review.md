# Code review

Review code changes against this skill's rules: architecture, traceability, agreement with the documents, tests and dependencies. Generic bug finding (logic errors, null handling, races) is the built-in `/code-review` skill's job; chain it when the user asks for a full review.

## Target

Same targets as `/code-review`:

| Given | Review |
| --- | --- |
| Nothing | Uncommitted changes (staged and unstaged) against `HEAD`; if there are none, the current branch against its merge base with `main` (or `master`) |
| A PR number | `gh pr diff <n>` |
| A branch | That branch against its merge base with `main` |
| A path | Those files or folders in full, not only their changes |

State the target in the first line of the report. Read whole files around each change; a diff alone hides where a rule is enforced.

## Process

1. **Full review, if asked** (`--full`): invoke the `code-review` skill with the same target (and the effort level, if the user gave one) and let it finish first. If it applies fixes or posts comments, that follows its own flags.
2. **Context.** Read `CLAUDE.md`, the rule IDs and use cases the changed code touches, the matching parts of `domain-model.md`, and the technical spec's stack table, folder layout and "which service enforces which rule" table. If `technical-spec.md` has a "Logging" section that adopts a policy, read `references/logging.md` and the "Personal data" section of `domain-model.md` too; the logging checks below then apply. If `docs/adoption.md` exists and the change is in an area it lists as not adopted, say so in the report and review that part only against the architecture baseline and the stack table, since it has no rules to check against yet. Find touched rules with `tools/rule_impact.py <IDs>` (or `<skill-dir>/scripts/` when the project has no `tools/` copy) and by the `@rule` tags in changed tests.
3. **Scripts first.** Run the project's architecture check (the command in `CLAUDE.md`; otherwise `check_imports.py` as the language reference describes) and `check_traceability.py --docs docs --tests <tests dir>`. Use the copies in `tools/`; when a script is missing there, run it from `<skill-dir>/scripts/` instead of skipping the check. Report only lines that concern the target, plus any failure that blocks the build. If a check cannot run, say which and why.
4. **Read** the changed code against the checklist below. Write findings down before fixing anything.
5. **Report**, then fix only with `--fix` (see Fixing).

## Checklist

### Architecture (`references/architecture.md`)

- Dependencies point inward: the domain imports no framework, ORM, HTTP, database or uncontrolled clock or random call; application services import no adapter.
- No business rule in a controller, template, SQL report, migration or adapter. A rule enforced in two places is a finding even if both agree.
- Ports only at real seams (persistence, clock, mail, external identity, storage); a new interface with one implementation and no test seam is a finding.
- Cross-aggregate checks live in the application layer, not inside one aggregate.
- Repositories return domain objects, not rows or query builders. Read-side queries hold no rules (architecture section 7).
- Errors are typed or English violation codes; no user-facing sentences in the domain.
- Nothing from the anti-pattern list (architecture section 8).

### Traceability

- Every changed or added piece of rule logic has a test citing its rule ID (`@rule AL-06`, tagged per the language reference).
- Tests cite only IDs that exist; changed tests still test what their tag claims. Read each tagged test against the rule text: a tag on a test that checks only part of the rule, or only a successful path, overstates coverage and is a finding, because the traceability script counts the tag as proof.
- A new use case class is listed in `use-cases.md` with its rule IDs; the technical spec's enforcement table names the class that now enforces each touched rule.

### Code matches the documents

- Names of classes, methods, fields, tables and routes follow the glossary in `domain-model.md`; no synonym for a glossary term.
- The rule logic does what the rule text in `business-rules.md` says, including limits, boundaries (inclusive or exclusive), roles and the error code returned.
- Every error code the code returns is in the code table, and a translation exists for it.
- Routes, permissions and schema match the technical spec. No endpoint, field or behaviour the documents do not define.

### Tests and dependencies

- Domain and service code has unit tests; each new adapter has integration tests against the real technology, never a mock or lookalike database.
- Tests assert behaviour named by a rule, not implementation details.
- Every new dependency (package manifest, lock file, import of an unlisted library) is in the technical spec's stack table. One that is not is a question for the user, never a silent addition.

### Logging (only if the project adopted a logging policy)

- Go through every item of the checklist in `references/logging.md` section 6 for each changed driving adapter, use case and port method, and report each miss as a `logging` finding.
- A personal-data value, secret or dumped object in a log entry is a `privacy` finding and goes first in the report, above architecture violations: it is a privacy breach, not a style issue.

## Report

Use this format, not the Build end-of-task report.

```
Target: <diff | PR #n | branch | path>
Checks: architecture <result> · traceability <result> · /code-review <ran | not requested>
Findings (most severe first):
  [architecture|privacy|traceability|docs|tests|dependency|logging] file:line - what is wrong - which rule or document it breaks (ID or section)
Code and documents disagree (decide which is right): <list or none>
Decisions needed from you: <list or none>
```

Order by severity: personal data in logs, architecture violations and rules outside the domain, then rule logic that contradicts the documents, then missing rule tests, then naming and table drift. If `/code-review` ran, merge its findings into the same ranked list once, dropping duplicates; when it has already shown its own findings, list only what it missed and say how many it reported.

## Fixing (`--fix` only)

Without `--fix`, report and stop.

With it, fix what is unambiguous: a missing `@rule` tag on a test that plainly tests that rule, a missing integration test, a rule moved from an adapter into the domain with its tests, an import that breaks the dependency rule. Run the tests and checks after the fixes and report real results.

Never fix on your own: code and documents that disagree (the documents are the source of truth until the user says otherwise, so ask which is right), a rename to a glossary term (that is a Change), a new or unlisted dependency, or anything that alters a rule or a decision. These go under "Decisions needed" as questions with a recommendation. Commit only if asked.
