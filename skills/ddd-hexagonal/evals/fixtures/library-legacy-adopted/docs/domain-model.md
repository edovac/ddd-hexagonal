# Library lending desk — Domain Model

2026-10-25 · lending desk maintainers

Concepts, boundaries and ownership of rules. It does not restate the specs. Only the adopted areas are modelled here; the others are listed in `adoption.md`.

- **What and why:** `functional-spec.md` · **Rules:** `business-rules.md` · **Use cases:** `use-cases.md`
- **How it is built:** `technical-spec.md`

## 1. Core domain

Lending: which member may take which book, until when, and how often a loan may be extended.

## 2. Ubiquitous language

One term, one meaning, in code, tests, tables and conversation.

| Code | Business term | Meaning |
| --- | --- | --- |
| `members`, `member_id` | Member | A registered borrower (LN-01). |
| `members.kind` | Member kind | `adult`, `child` or `staff`; decides the loan period (LN-07). |
| `members.suspended` | Suspended | A member who may not borrow (LN-02). Set and lifted by the Fees and suspension area. |
| `books`, `book_id` | Book | A copy in the catalogue (LN-03). |
| `books.reference_only` | Reference-only book | A book that stays in the library (LN-04). |
| `loans` | Loan | One book lent to one member. |
| `returned_on IS NULL` (`open_loans`) | Open loan | A loan not returned yet (LN-05, LN-06). |
| `lent_on` | Lending date | The day the loan is made. |
| `due_on` | Due date | The day the book is due back (LN-07, LN-10). |
| – | Overdue | A loan past its due date (LN-09). |
| `renew`, `renewals` | Renewal | Moving a loan's due date forward (LN-08 to LN-11). |
| `give_back`, `returned_on`, route `/return` | Return | Closing the loan when the book comes back. |

Avoid: "give back" (use "return"; renaming `give_back` in code is a later Change).

## 3. Bounded contexts

| Context | Responsibility | Tables or stores | Status |
| --- | --- | --- | --- |
| **Lending** (core) | Loans, due dates, renewals, returns | `loans` | adopted |
| Fees and suspension | Late fees, payments, suspension | `members.fees_owed`, `members.suspended` | not adopted |
| Membership | Registering members | `members` | not adopted |
| Catalog | Adding books | `books` | not adopted |

Relationships: Lending reads a member's kind and suspension and a book's reference-only flag, by ID. Today the return calls into Fees directly (`src/library/loans.py:58-64`).

## 4. Aggregates

| Aggregate | Root and children | Guarantees (rule IDs) |
| --- | --- | --- |
| **Loan** | Loan (no children) | LN-07, LN-08, LN-09, LN-10, LN-11, LN-12 |

Rules across loans, guarded when a loan is opened (a lending service, not one aggregate): LN-05 (open loans of a member) and LN-06 (open loans of a book). Checks on other aggregates' state at lending: LN-01 to LN-04. Where each rule is enforced today: `technical-spec.md` "Business logic".

## 5. Value objects

None yet. Candidates for the restructuring Change: `DueDate` / loan period by member kind (LN-07, LN-10).

## 6. Services and application layer

- Today: none; `src/library/loans.py` mixes SQL and rules, `src/library/web.py` calls it.
- Target: one application class per use case in `use-cases.md`, shaped load → guard → apply → save (`technical-spec.md` "Architecture").

Dependency direction: driving adapters → application → domain ← driven adapters.

## 7. Ports

None today. Expected when Lending moves to the target layout:

| Port | Why it exists (second implementation or test seam) | Adapter |
| --- | --- | --- |
| `LoanRepository` | Persistence of the Loan aggregate; in-memory fake for unit tests | PostgreSQL (psycopg) |
| `Clock` | Today's date, used by LN-07, LN-09 and the return (`date.today()` in `src/library/loans.py:21,42,56`) | System clock |

## 8. Domain events

None. Vocabulary for later: loan opened, loan renewed, book returned.

## 9. Personal data

Never in logs (`technical-spec.md` "Logging").

| Aggregate or value object | Field | Category |
| --- | --- | --- |
| Member | `name` | personal |
| Member | `email` | personal |
| Member | `fees_owed`, `suspended` | personal |

## 10. Testing the model

Lending is pinned by characterization tests through `src/library/loans.py` and the Flask routes (`tests/integration/test_lending.py`). Unit tests come with the domain classes.

## 11. How to use this file

- Before a feature, find its concept in section 2 and its home in section 3.
- A new rule is first added to `business-rules.md` with an ID, then goes into an aggregate or domain service with a unit test.
- When a term in code and in the glossary diverge, rename the code (through Change).
