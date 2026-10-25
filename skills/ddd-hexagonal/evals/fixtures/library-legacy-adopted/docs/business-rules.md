# Library lending desk — Business Rules

2026-10-25 · lending desk maintainers

The single home of every business rule. Other documents refer to a rule by its ID and never restate it. Tests cite the ID (`@rule LN-06`). The Code column is the English code a failed check returns; the user-facing message for each code lives in the translation files.

Only adopted areas have rules here; the others are listed in `adoption.md`.

## Lending (LN)

| ID | Rule | Code |
| --- | --- | --- |
| LN-01 | A loan is made only to a registered member; a request for an unknown member is rejected. | `member_not_found` |
| LN-02 | A suspended member cannot borrow. | `member_suspended` |
| LN-03 | A loan is made only for a book in the catalogue; a request for an unknown book is rejected. | `book_not_found` |
| LN-04 | A reference-only book cannot be lent. | `book_reference_only` |
| LN-05 | A member has at most 3 open loans at a time; a request that would make a 4th is rejected. Returned loans do not count. | `loan_limit_reached` |
| LN-06 | A book is on at most one open loan at a time. | `book_on_loan` |
| LN-07 | The due date is the lending date plus 21 days for an adult or staff member, and plus 14 days for a child. | – |
| LN-08 | A returned loan cannot be renewed. | `loan_returned` |
| LN-09 | An overdue loan cannot be renewed; a loan is overdue from the day after its due date, so it can still be renewed on the due date. | `loan_overdue` |
| LN-10 | A renewal for an adult or staff member moves the due date 21 days past the current due date, not past the renewal date. | – |
| LN-11 | A loan is renewed at most 2 times. | `renewal_limit_reached` |
| LN-12 | A returned loan cannot be returned again. | `loan_returned` |

Gaps in this area:

- **No error code yet.** The codes above are proposed; today the code returns English sentences or an HTTP 500 (`technical-spec.md` "Business logic", column "Today on failure"). Returning the codes is a Change.
- LN-12: the code does not enforce it (open point in `functional-spec.md`).
- How a child's renewal is counted, and whether a suspended member may renew, are open points in `functional-spec.md`; no rule yet.
