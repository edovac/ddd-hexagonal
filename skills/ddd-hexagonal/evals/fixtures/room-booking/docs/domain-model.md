# Room Booking — Domain Model

2026-10-01 · Space manager

Concepts, boundaries and ownership of rules. It does not restate the specs.

- **What and why:** `functional-spec.md` · **Rules:** `business-rules.md` · **Use cases:** `use-cases.md`
- **How it is built:** `technical-spec.md`

## 1. Core domain

A room is never booked twice for the same time (BK-02).

## 2. Ubiquitous language

| Code | Interface term | Meaning |
| --- | --- | --- |
| `Member` | Member | A person with a login at the space, known here only by ID |
| `Room` | Room | A bookable meeting room |
| `Booking` | Booking | A room held by one member for one period; active or cancelled |
| `BookingPeriod` | Time | Half-open interval from start to end, in UTC (BK-02, BK-04, BK-05) |
| Upcoming booking | Upcoming | An active booking whose start is after the current time (BK-01) |

Avoid: "reservation" (use booking), "slot" (use period).

## 3. Bounded contexts

| Context | Responsibility | Tables or stores |
| --- | --- | --- |
| **Booking** (core) | Rooms and bookings | `rooms`, `bookings` |

Relationships: members come from the space's login and are referenced by ID only.

## 4. Aggregates

| Aggregate | Root and children | Guarantees (rule IDs) |
| --- | --- | --- |
| **Booking** | `Booking` (no children) | BK-04, BK-05 through its period; BK-06, BK-07 on cancel |

BK-01, BK-02 and BK-03 span several bookings or need the clock, so the application layer checks them (`BookRoom`) through a domain service.

## 5. Value objects

| Class | Rules |
| --- | --- |
| `BookingPeriod` | Timezone-aware start and end, half-open; BK-04, BK-05 on construction |

## 6. Services and application layer

- Domain service: booking policy for BK-01, BK-02, BK-03, given the counts and periods the application loads.
- Application classes: one per use case in `use-cases.md`, shaped authorise → load → guard → apply → save.

Dependency direction: driving adapters → application → domain ← driven adapters.

## 7. Ports

| Port | Why it exists (second implementation or test seam) | Adapter |
| --- | --- | --- |
| `BookingRepository` | Persistence of the aggregate; in-memory fake for unit tests | PostgreSQL |
| `RoomRepository` | Room lookup for RM-01; in-memory fake for unit tests | PostgreSQL |
| `Clock` | BK-01 and BK-03 depend on the current time | System clock |

## 8. Domain events

`BookingMade`, `BookingCancelled`: vocabulary only; no dispatcher in milestone 1.

## 9. Personal data

| Aggregate or value object | Field | Category |
| --- | --- | --- |
| `Booking` | `member_id` | Personal (pseudonymous ID) |

## 10. Testing the model

- Boundaries of BK-02 (touching periods) and BK-04 (exactly 8 hours) each have their own test.

## 11. How to use this file

- Before a feature, find its concept in section 2 and its home in section 3.
- A new rule is first added to `business-rules.md` with an ID, then goes into an aggregate or domain service with a unit test.
- When a term in code and in the glossary diverge, rename the code.
