# Room Booking — Use Cases

2026-10-01 · Space manager

Who does what, in which order. A use case holds no rule of its own: it names the rules it applies by ID, and `business-rules.md` states them. A build task is one use case.

**Home** is where the code lives: a class in the application layer unless another folder is named. Every use case that changes data runs in one transaction.

## Bookings

| ID | Use case | Actor | Main flow | Rules | Home |
| --- | --- | --- | --- | --- | --- |
| UC-01 | Book a room | Member | Choose room, start and end → checks → booking saved → booking ID returned | RM-01, BK-01, BK-02, BK-03, BK-04, BK-05 | `BookRoom` |
| UC-02 | Cancel a booking | Member | Choose own booking → checks → booking marked cancelled | BK-06, BK-07, BK-08 | `CancelBooking` |

Alternative flows: a failed check returns its code and saves nothing.
