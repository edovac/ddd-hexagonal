# Library lending desk — Functional Specification

2026-10-25 · lending desk maintainers

What the system does and why. Rules are in `business-rules.md` and are referenced here by ID, never restated. Flows are in `use-cases.md`. Implementation is in `technical-spec.md`.

This spec covers the adopted areas only; the rest of the application is described in `adoption.md` until it is adopted.

## Purpose and context

The lending desk app of the town library: the front desk registers members, adds books, lends, renews and takes back books. About three years old; the original author has left and there were no documents, so the rules were read from the code and confirmed (2026-10-25).

- **Users:** front desk staff.
- **Interface:** JSON HTTP API (Flask); no screens in this repository.
- **Hosting and maintenance:** not known (open point).

## Users and roles

| Role | Can do | Sees |
| --- | --- | --- |
| Front desk staff | UC-01, UC-02, UC-03 | members, books, loans |

The app has no login or role check; anyone who reaches the server can do everything (open point).

## Core concepts

A member borrows a book on a loan, which has a due date and may be renewed; the loan stays open until the book is returned. Terms are in `domain-model.md` section 2.

## Behaviour

### Lending

- Lending (UC-01): the desk enters a member and a book; the loan opens today with a due date that depends on the member's kind. Rules: LN-01 to LN-07.
- Renewal (UC-02): the desk extends an open loan that is not overdue. Rules: LN-08 to LN-11.
- Return (UC-03): the desk closes the loan; the response gives the late fee charged (Fees and suspension area, not adopted yet). Rule: LN-12.

## Scope and rollout

**Out of scope**

- Not adopted yet, see `adoption.md`: Fees and suspension, Members, Catalog.

**Open points**

- [ ] **LN-12, code differs from rule:** a returned loan can be returned again; the second return overwrites the return date and charges the late fee again (`src/library/loans.py:55-66`). Test: `tests/integration/test_lending.py::test_returned_loan_cannot_be_returned_again` (expected failure). Next Change.
- [ ] **Child renewals:** a renewal adds 21 days for every member kind, children included (`src/library/loans.py:48-50`), while a child's first loan is 14 days (LN-07). Which is intended? Head librarian.
- [ ] **Suspended members renewing:** renewal does not check suspension (`src/library/loans.py:41-52`), lending does (LN-02). Allowed or not? Head librarian.
- [ ] **Unclean failures:** some checks end in an HTTP 500 (`technical-spec.md` "Business logic"), and so does renewing or returning an unknown loan ID (`src/library/loans.py:43-44,57-58`). No check returns an error code (`business-rules.md` gaps).
- [ ] **Dead second loan limit:** `src/library/web.py:8,47` checks 5 open loans before `loans.lend` checks 3 (LN-05); the 5 never takes effect. Remove in a Change.
- [ ] **Limit not atomic:** LN-05 counts open loans and then inserts without a lock, so two lends at the same moment can pass 3.
- [ ] **No authentication:** who may use the app, and how staff log in. Library management.
- [ ] **Hosting, backup, log retention:** where the app runs, how the database is backed up, how long logs are kept. Whoever runs the server.

**Rollout** (progress is in `plan.md`)

1. Adopt Lending: LN-01 to LN-12, UC-01 to UC-03.
2. Adopt Fees and suspension, then Members and Catalog.
