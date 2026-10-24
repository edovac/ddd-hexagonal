# Returns Desk

Return requests and refunds for an online homeware shop.

## Specs — read before making changes

- @docs/functional-spec.md — what the system does and why
- @docs/business-rules.md — every business rule, with an ID; the single home of rules
- @docs/use-cases.md — who does what; one task = one use case
- @docs/technical-spec.md — how it is built
- @docs/domain-model.md — language, aggregates, ports

The specs are the source of truth. If code and spec disagree, ask before changing either.

## Coding rules

- Commands: unit `npx vitest run` · traceability `uv run tools/check_traceability.py --docs docs --tests tests`
