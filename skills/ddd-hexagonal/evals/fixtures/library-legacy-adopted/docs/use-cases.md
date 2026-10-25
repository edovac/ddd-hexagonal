# Library lending desk — Use Cases

2026-10-25 · lending desk maintainers

Who does what, in which order. A use case holds no rule of its own: it names the rules it applies by ID, and `business-rules.md` states them. A build task is one use case.

**Home** is where the code lives today. In an adopted area that is still the original module; it moves when a Change restructures the code. Every use case that changes data runs in one transaction.

## Lending

| ID | Use case | Actor | Main flow | Rules | Home |
| --- | --- | --- | --- | --- | --- |
| UC-01 | Lend a book | Front desk staff | Member ID and book ID → checks → loan opened with lending date today and its due date → loan ID | LN-01, LN-02, LN-03, LN-04, LN-05, LN-06, LN-07 | `src/library/web.py::lend` → `src/library/loans.py::lend` |
| UC-02 | Renew a loan | Front desk staff | Loan ID → checks → renewal counted, due date moved | LN-08, LN-09, LN-10, LN-11 | `src/library/web.py::renew` → `src/library/loans.py::renew` |
| UC-03 | Return a book | Front desk staff | Loan ID → return date set to today, loan closed → late fee returned | LN-12 | `src/library/web.py::give_back` → `src/library/loans.py::give_back` |

Alternative flows:

- UC-03 also charges the late fee and may suspend the member. That logic belongs to the Fees and suspension area, not adopted yet (`adoption.md`).
