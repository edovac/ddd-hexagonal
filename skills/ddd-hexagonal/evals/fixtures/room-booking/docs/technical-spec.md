# Room Booking — Technical Specification

2026-10-01 · Space manager

How the system in `functional-spec.md` is built. It says which service enforces which rule by ID; rule text is in `business-rules.md`.

## Architecture

```
(milestone 2: HTTP) -> application -> domain <- persistence (PostgreSQL), system clock
```

Milestone 1 has no driving adapter; use cases are exercised by tests.

## Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.12, managed with uv |
| Framework | None in milestone 1 |
| Database | PostgreSQL 16 |
| Database driver | psycopg 3 (`psycopg[binary]`) |
| Tests | pytest, mypy (strict), ruff, import-linter |

A dependency not listed here needs the user's approval before use.

## Hosting constraints

- One VPS with 1 GB of memory; PostgreSQL 16 runs on the same host.
- A single application process; no queue or cache.

## Project structure

```
src/roombooking/
├── domain/                 booking, period, policy, errors (standard library only)
├── application/            one class per use case
│   └── ports.py            BookingRepository, RoomRepository, Clock
├── adapters/
│   ├── persistence/        PostgreSQL repositories
│   └── clock.py            system clock
└── bootstrap.py            composition root
migrations/                 numbered SQL files, applied in order
tests/
├── unit/                   domain and application, with in-memory fakes
└── integration/            adapters and use cases against PostgreSQL
```

## Database schema

Migrations in `migrations/`. `bookings.status` is `active` or `cancelled`. The exclusion constraint `bookings_no_overlap` (GiST on room and `tstzrange(starts_at, ends_at, '[)')`, active rows only) backs BK-02 when two requests arrive at the same time; it needs the `btree_gist` extension.

## Routes and permissions

None in milestone 1; see the open point in the functional spec.

## Business logic

### `BookRoom` (UC-01)

Enforces RM-01, BK-01, BK-02, BK-03 through the booking policy, and BK-04, BK-05 through `BookingPeriod`. BK-02 is also enforced by `bookings_no_overlap`; the repository turns that violation into `room_already_booked`.

### `CancelBooking` (UC-02)

Enforces BK-06, BK-07 through the `Booking` aggregate. BK-08 is enforced by the repository queries and by `bookings_no_overlap`, which consider active rows only.

## Authentication and security

Milestone 2. Until then use cases take the member ID as input.

## Logging

Out of scope for milestone 1, decided at Bootstrap.

## Operations

- Migrations are applied in file order; a migration applied to any environment is never edited.
- Daily `pg_dump`, kept 30 days.

## Decisions

- **D-1 Overlap check in the database.** BK-02 is backed by a PostgreSQL exclusion constraint so that two simultaneous requests cannot both succeed. Rejected: a lock on the room row in the application (more code, easy to forget in a new use case).

## Testing

- **Unit:** every business rule in the domain and service layers; no database, no framework.
- **Integration:** adapters and use cases against PostgreSQL 16 (`docker compose up -d db`), schema from the migrations, each test rolled back.
- **Manual before release:** none in milestone 1.

Rules:

- **Test first** for the domain and service layers.
- **Rule reference:** each test names the rules it covers, `@rule BK-01`, and the use case, `@usecase UC-01`. A rule ID without a test is reported as a gap.
- **Gate:** the pipeline stops on a failing test, static analysis error or architecture check failure.

## Conventions

- Everything in code is English: identifiers, database names, config keys, comments, tests, error codes, commits.
- Times are timezone-aware and stored as `timestamptz`; the domain works in UTC.
- ruff with the rule set in `pyproject.toml`; mypy `strict = true`.
