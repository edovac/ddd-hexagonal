# Library lending desk — Adoption

2026-10-25 · lending desk maintainers

Working file while existing code is brought under the workflow (`references/adopt.md` in the ddd-hexagonal skill). It holds the map of areas and the candidates of the area in progress. Candidates are not rules: a rule exists only once the user confirms it and it moves to `business-rules.md`. Delete this file when every area is adopted.

## Starting state

| Item | Value |
| --- | --- |
| Commit | `04764ca` (Lending desk 0.3.2) |
| Test suite | `uv run pytest`: 2 passed, 1 failed |
| Tests failing before adoption | `tests/test_fees.py::test_fee_is_capped` expects a 15.00 cap, `src/library/fees.py:2` caps at 10.00. Fees area; not fixed by Adopt |
| Layering found | none: flat modules mixing SQL and rules (`loans.py`, `members.py`, `catalog.py`), pure `fees.py`, Flask routes in `web.py`, connection in `db.py` |
| Architecture baseline | 0 known violations (`uv run lint-imports`, see `technical-spec.md` "Architecture check") |

## Areas

| Area | Entry points | Main tables | Status | Rules | Use cases |
| --- | --- | --- | --- | --- | --- |
| Lending | `POST /loans`, `POST /loans/<id>/renewal`, `POST /loans/<id>/return` | `loans` (reads `members`, `books`) | adopted 2026-10-25 | LN-01 to LN-12 | UC-01 to UC-03 |
| Fees and suspension | `POST /members/<id>/payments`; fee charging inside `POST /loans/<id>/return` | `members.fees_owed`, `members.suspended` | not adopted | | |
| Members | `POST /members` | `members` | not adopted | | |
| Catalog | `POST /books` | `books` | not adopted | | |

External systems: none (no mail, payment or identity provider).

## Notes for areas not adopted yet

Found while tracing Lending; to be traced and confirmed when the area is adopted.

**Fees and suspension**

- The return charges a late fee: `late_fee((today - due_on).days)`, `src/library/loans.py:58`; 0.25 per day late, capped at 10.00, `src/library/fees.py:1-8`. The existing test expects a 15.00 cap (`tests/test_fees.py:12-13`, failing).
- The fee is added to `members.fees_owed`, and a member owing more than 20 is suspended, `src/library/loans.py:60-64`.
- Fees are computed on `float` (`src/library/fees.py:1-2`, `src/library/web.py:26`) and stored as `NUMERIC(8, 2)`.
- A payment lowers what is owed, never below 0, and lifts the suspension when nothing is owed, `src/library/members.py:22-28`.

**Members**

- Name required, e-mail format check, e-mail stored lower-case, `src/library/members.py:3-16`; e-mail unique and kind in `adult`, `child`, `staff`, `migrations/001_init.sql:4-5`.

**Catalog**

- ISBN hyphens removed, 10 or 13 characters, all but the last a digit, `src/library/catalog.py:6-8`; ISBN unique, `migrations/001_init.sql:12`.
