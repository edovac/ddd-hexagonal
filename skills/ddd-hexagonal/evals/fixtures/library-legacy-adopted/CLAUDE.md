# Library lending desk

Flask + PostgreSQL lending desk for the town library, being brought under DDD and hexagonal architecture one area at a time (`docs/adoption.md`).

## Specs — read before making changes

- @docs/functional-spec.md — what the system does and why
- @docs/business-rules.md — every business rule, with an ID; the single home of rules
- @docs/use-cases.md — who does what, step by step; one task = one use case
- @docs/technical-spec.md — how it is built
- @docs/domain-model.md — language, bounded contexts, aggregates, ports
- @docs/adoption.md — which areas are adopted; Build and Change apply to adopted areas only

The specs are the source of truth. If code and spec disagree, ask before changing either.

## Documentation rules

- Each fact lives in exactly one document; the others link to it, never restate it.
- Division of labour: functional spec = what and why; business rules = the rules, with IDs; use cases = flows that reference rule IDs; domain model = language, boundaries, ownership; technical spec = how.
- Keep documents short: tables and bullets over prose, a pointer over a copy.
- After each use case run the light documentation review; after each milestone, the deep review (skill `ddd-hexagonal`, `references/doc-review.md`).

## Key constraints

Stack, conventions and testing rules are in `technical-spec.md`. Read them before writing code.

## Coding rules

- Code, comments, identifiers, database names, routes, error codes and commit messages in English; user-visible text in templates or translation files.
- Hexagonal-lite: ports only at real seams (persistence, clock, mail).
- Test first for domain and service code. Integration tests run against the real PostgreSQL (`DATABASE_URL`), never a substitute. No coverage percentage; CI stops on a failing test or architecture check.
- Commands: all tests `uv run pytest` · integration `DATABASE_URL=postgresql://postgres:test@localhost:5433/library uv run pytest tests/integration` · static analysis: none yet · architecture `uv run lint-imports` · traceability `uv run tools/check_traceability.py --docs docs --tests tests`
- Known red test at adoption: `tests/test_fees.py::test_fee_is_capped` (Fees area, not adopted yet).
- Reports: concise. Concise is the mode's report block and the decisions needed; detailed adds a short explanation per finding.
- Before calling a task done: run all of them and report the real result, including failures; give the rule and use-case IDs touched, the test covering each, and any gap or mismatch. If code and spec disagree, ask before changing either.

## Logging

Logging follows `technical-spec.md` "Logging" for new and moved code: one DEBUG on entry and one INFO on completion per adapter call and use case, a correlation ID on every entry, no logging in the domain, never personal data (see `domain-model.md` "Personal data").

## Git and dependencies

- Before changing code, check the current branch. If it is the main branch, propose a new branch name and ask before creating it: `<mode>/<short-slug>`, e.g. `adopt/fees`, `change/loan-limit`. Never commit to the main branch.
- Commit only when asked. Commit messages are in English.
- A dependency not listed in the technical spec's Stack table needs the user's approval first; once approved, add it to that table.
- The architecture baseline (`ignore_imports` in `pyproject.toml`) only shrinks; adding an entry needs the user's approval.
