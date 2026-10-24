from collections.abc import Iterable
from datetime import datetime

from roombooking.domain.booking import BookingPeriod
from roombooking.domain.errors import BookingRejected

MAX_UPCOMING_BOOKINGS = 3  # BK-01


def check_new_booking(
    period: BookingPeriod,
    now: datetime,
    upcoming_for_member: int,
    active_periods_of_room: Iterable[BookingPeriod],
) -> None:
    """Rules that span several bookings or need the clock: BK-01, BK-02, BK-03."""
    if period.starts_at <= now:
        raise BookingRejected("booking_in_past")  # BK-03
    if upcoming_for_member >= MAX_UPCOMING_BOOKINGS:
        raise BookingRejected("too_many_upcoming_bookings")  # BK-01
    if any(period.overlaps(other) for other in active_periods_of_room):
        raise BookingRejected("room_already_booked")  # BK-02
