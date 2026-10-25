# Library lending desk — Technical Specification

2026-10-25 · lending desk maintainers

How the system in `functional-spec.md` is built. It says which component enforces which rule by ID; rule text is in `business-rules.md`.

## Architecture

**As found** (commit `04764ca`): no layering.

```
web.py (Flask routes)  ->  loans.py, members.py, catalog.py (rules + SQL)  ->  PostgreSQL
                                  loans.py -> fees.py (pure calculation)
db.py: connection from DATABASE_URL
```

**Target** for new and moved code (hexagonal-lite, Python reference layout):

```
src/library/
├── domain/            entities, value objects, domain services, errors (standard library only)
├── application/       one class per use case; ports.py holds the Protocols
├── adapters/
│   ├── web/           Flask routes
│   └── persistence/   psycopg repositories
├── queries/           read side
└── bootstrap.py       composition root
```

Driving adapters → application → domain ← driven adapters. Ports only at real seams (`domain-model.md` section 7).

## Stack

As found in `pyproject.toml` and `docker-compose.yml`, plus what was approved since.

| Layer | Choice |
| --- | --- |
| Language | Python ≥ 3.12 (`requires-python`) |
| Project and dependencies | uv, `uv.lock` committed; build backend hatchling |
| Framework | Flask ≥ 3.0 |
| Database driver | psycopg[binary] ≥ 3.2 |
| Database | PostgreSQL 16 (`docker-compose.yml`) |
| Tests | pytest ≥ 8 (dev) |
| Architecture check | import-linter ≥ 2.15 (dev; approved 2026-10-25, D-1) |
| Static analysis | none yet (no type checker or linter in the project) |

A dependency not listed here needs the user's approval before use.

## Hosting constraints

- Not known; see the open points in `functional-spec.md`.

## Project structure

```
migrations/          SQL migrations, applied in file order
src/library/         application code (as found, see Architecture)
tests/               test_fees.py (existing, Fees area)
tests/integration/   real-PostgreSQL tests; conftest.py creates a schema per session
tools/               check_traceability.py, check_imports.py, rule_impact.py
```

## Database schema

`migrations/001_init.sql`. Constraints that are Lending rules:

| Constraint | Rule |
| --- | --- |
| `loans.member_id REFERENCES members(id)` | LN-01 |
| `loans.book_id REFERENCES books(id)` | LN-03 |
| `one_open_loan_per_book` unique index on `loans (book_id) WHERE returned_on IS NULL` | LN-06 |
| `CHECK (renewals <= 2)` | LN-11 |

## Routes and permissions

No route checks who calls it (open point in `functional-spec.md`).

| Method | Path | Purpose | Role |
| --- | --- | --- | --- |
| POST | `/loans` | UC-01 Lend a book | anyone who reaches the server |
| POST | `/loans/<id>/renewal` | UC-02 Renew a loan | anyone who reaches the server |
| POST | `/loans/<id>/return` | UC-03 Return a book | anyone who reaches the server |
| POST | `/members` | Register a member (not adopted) | anyone who reaches the server |
| POST | `/members/<id>/payments` | Pay fees (not adopted) | anyone who reaches the server |
| POST | `/books` | Add a book (not adopted) | anyone who reaches the server |

## Business logic

Which component enforces which rule today. No rule text.

| Rule | Enforced at | Today on failure |
| --- | --- | --- |
| LN-01 | `src/library/loans.py:23-24`; FK `migrations/001_init.sql:19` | `LoanError`, HTTP 409 |
| LN-02 | `src/library/loans.py:25-26` | `LoanError`, HTTP 409 |
| LN-03 | FK `migrations/001_init.sql:20` only; `src/library/loans.py:27-28` crashes first on the missing row | `TypeError`, HTTP 500 |
| LN-04 | `src/library/loans.py:28-29` | `LoanError`, HTTP 409 |
| LN-05 | `src/library/loans.py:5,30` (3); also `src/library/web.py:8,47` with 5, which never takes effect | `LoanError`, HTTP 409 |
| LN-06 | unique index `migrations/001_init.sql:28` only; to be enforced in the domain as well (decided 2026-10-25) | `UniqueViolation`, HTTP 500 |
| LN-07 | `src/library/loans.py:6-7,32-35` | – |
| LN-08 | `src/library/loans.py:44-45` | `LoanError`, HTTP 409 |
| LN-09 | `src/library/loans.py:46-47` | `LoanError`, HTTP 409 |
| LN-10 | `src/library/loans.py:48-50` | – |
| LN-11 | `CHECK` `migrations/001_init.sql:23` only; to be enforced in the domain as well (decided 2026-10-25) | `CheckViolation`, HTTP 500 |
| LN-12 | not enforced (`src/library/loans.py:55-66`; open point) | second return accepted, fee charged again |

## Authentication and security

None: no login, no role check on any route (open point in `functional-spec.md`).

## Logging

Adopted 2026-10-25 for new and moved code: follows the skill's logging policy (one DEBUG on entry, one INFO on completion per adapter call and use case, correlation ID, no personal data). The existing code logs nothing and is not changed by Adopt.

| Item | Choice |
| --- | --- |
| Library and format | standard library `logging`, JSON formatter in the composition root (a formatter library needs approval) |
| Destination | stdout, collected by the host |
| Level per environment | production INFO · local and test DEBUG |
| Retention | open point (`functional-spec.md`) |
| Correlation ID header | `X-Correlation-Id` |

## Operations

- Database: `docker compose up -d db`, then apply `migrations/*.sql` with `psql` (README). No migration tool.
- Run: `DATABASE_URL=... uv run flask --app library.web run`.
- Backup and deploy: not known (open point).

## Architecture check

`uv run lint-imports`, configured in `pyproject.toml`:

- "Layers point inward (target layout)": `library.adapters` → `library.application` → `library.domain`, all optional until the folders exist.
- "Rule modules use no web framework": `library.loans`, `library.members`, `library.catalog`, `library.fees` may not import `flask`.
- When `src/library/domain/` is created, add a forbidden contract keeping `flask` and `psycopg` out of `library.domain` and `library.application` (import-linter rejects a source module that does not exist yet).

**Baseline:** 0 known violations (2026-10-25). Known violations go in each contract's `ignore_imports`, exact module names only. The count only goes down; adding an entry needs the user's approval.

## Decisions

- **D-1 import-linter as the architecture check.** The Python reference's tool; checks real and indirect imports. Rejected: `tools/check_imports.py` (sees import lines only).

## Testing

- **Unit:** every business rule in the domain and service layers; no database, no framework. None yet for Lending: its rules are only reachable through `src/library/loans.py`, which needs a connection.
- **Integration:** `tests/integration/`, against the real PostgreSQL named by `DATABASE_URL`. `conftest.py` creates a schema per session, applies `migrations/*.sql`, empties the tables after each test (the code under test commits) and drops the schema. Without `DATABASE_URL` the integration tests are skipped, so CI must set it.
- **Expected failures:** `pytest.mark.xfail(strict=True)` citing the rule and the open point; the marker is removed by the Change that fixes the code.
- **Commands:** `uv run pytest` (all) · `DATABASE_URL=postgresql://postgres:test@localhost:5433/library uv run pytest tests/integration` · `uv run lint-imports` · `uv run tools/check_traceability.py --docs docs --tests tests`

Rules:

- **Test first** for the domain and service layers.
- **Rule reference:** each test names the rules it covers, `@rule LN-01`, and the use case, `@usecase UC-01`.
- **Gate:** the pipeline stops on a failing test or architecture check failure. Known red test at adoption: `tests/test_fees.py::test_fee_is_capped` (Fees area).

## Conventions

- Everything in code is English: identifiers, database names, routes, config keys, comments, tests, error codes, commits. User-visible text lives in templates and translation files.
- Dates are the server's local date (`date.today()`).
