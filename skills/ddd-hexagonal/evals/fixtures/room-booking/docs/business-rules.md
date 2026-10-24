# Room Booking — Business Rules

2026-10-01 · Space manager

The single home of every business rule. Other documents refer to a rule by its ID and never restate it. Tests cite the ID (`@rule BK-01`). The Code column is the English code a failed check returns; the user-facing message for each code lives in the translation files.

## Bookings (BK)

| ID | Rule | Code |
| --- | --- | --- |
| BK-01 | A member holds at most 3 upcoming bookings; a request for a 4th is rejected. | `too_many_upcoming_bookings` |
| BK-02 | Two active bookings of the same room never overlap. Periods are half-open: a booking that ends exactly when another starts does not overlap it. | `room_already_booked` |
| BK-03 | A booking starts after the current time. | `booking_in_past` |
| BK-04 | A booking lasts at most 8 hours; exactly 8 hours is allowed. | `booking_too_long` |
| BK-05 | A booking ends after it starts. | `invalid_period` |
| BK-06 | Only the member who made a booking cancels it. | `not_booking_owner` |
| BK-07 | A booking is cancelled only before it starts. | `booking_already_started` |
| BK-08 | A cancelled booking counts for neither BK-01 nor BK-02. | – |

## Rooms (RM)

| ID | Rule | Code |
| --- | --- | --- |
| RM-01 | A booking names a room that exists. | `room_not_found` |
