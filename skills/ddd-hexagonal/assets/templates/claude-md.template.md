# <Project>

<One-line description.>

## Specs — read before making changes

- @docs/functional-spec.md — what the system does and why
- @docs/business-rules.md — every business rule, with an ID; the single home of rules
- @docs/use-cases.md — who does what, step by step; one task = one use case
- @docs/technical-spec.md — how it is built
- @docs/domain-model.md — language, bounded contexts, aggregates, ports

The specs are the source of truth. If code and spec disagree, ask before changing either.

## Documentation rules

- Each fact lives in exactly one document; the others link to it, never restate it.
- Division of labour: functional spec = what and why; business rules = the rules, with IDs; use cases = flows that reference rule IDs; domain model = language, boundaries, ownership; technical spec = how.
- Keep documents short: tables and bullets over prose, a pointer over a copy.
- After each use case run the light documentation review; after each milestone, the deep review (skill `ddd-hexagonal`, `references/doc-review.md`).

## Key constraints

Hosting limits, stack, conventions and testing rules are in `technical-spec.md`. Read them before writing code.

## Coding rules

- Test first for domain and service code. Integration tests run against the real database.
- Commands: unit `<cmd>` · integration `<cmd>` · static analysis `<cmd>` · architecture `<cmd>` · traceability `python tools/check_traceability.py --docs docs --tests <tests dir>`
- Before calling a task done: run all of them and report the real result, including failures; give the rule and use-case IDs touched, the test covering each, and any gap or mismatch. If code and spec disagree, ask before changing either.

## Git and dependencies

- Before changing code, check the current branch. If it is the main branch, propose a new branch name and ask before creating it. Never commit to the main branch.
- Commit only when asked. Commit messages are in English.
- A dependency not listed in the technical spec's Stack table needs the user's approval first; once approved, add it to that table.
