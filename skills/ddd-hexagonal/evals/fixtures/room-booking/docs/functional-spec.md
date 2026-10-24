# Room Booking — Functional Specification

2026-10-01 · Space manager

What the system does and why. Rules are in `business-rules.md` and are referenced here by ID, never restated. Flows are in `use-cases.md`. Implementation is in `technical-spec.md`.

## Purpose and context

Members of a coworking space book its meeting rooms by the hour, so that two groups never turn up for the same room at the same time and no member holds rooms they will not use.

- **Users:** about 150 members today, one space with 6 rooms.
- **Context:** bookings are handled on a shared spreadsheet today, with frequent double bookings.
- **Interface:** English; the interface itself is decided in milestone 2.
- **Hosting and maintenance:** one small VPS run by the space; details in the technical spec.

## Users and roles

| Role | Can do | Sees |
| --- | --- | --- |
| Member | Book a room, cancel own bookings | Own bookings |

Access rules: BK-06.

## Core concepts

A **member** books a **room** for a **period**; the result is a **booking**. A booking is active until it is cancelled.

## Behaviour

### Booking a room

- The member picks a room, a start and an end, and gets the booking back or the reason it was refused.

Rules: RM-01, BK-01, BK-02, BK-03, BK-04, BK-05.

### Cancelling a booking

- The member picks one of their bookings and cancels it; the room is free again.

Rules: BK-06, BK-07, BK-08.

## Reports and exports

None in milestone 1.

## Privacy, retention and backup

- The system stores only the member's ID from the space's existing login, never names or contact details.
- Daily database backup, kept 30 days.

## Scope and rollout

**Out of scope**

- Payments and pricing.
- Recurring bookings.
- Room administration: rooms are created by a database migration.
- Audit log.

**Open points**

- [ ] HTTP interface and authentication against the space's login (milestone 2) — space manager.
- [ ] Should a no-show free the room after 15 minutes? — space manager.

**Rollout** (each step is a milestone for the deep documentation review)

1. Domain, application and persistence: UC-01, UC-02.
2. HTTP interface.
