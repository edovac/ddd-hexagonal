from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from roombooking.domain.errors import BookingRejected

MAX_BOOKING_DURATION = timedelta(hours=8)  # BK-04


@dataclass(frozen=True)
class BookingPeriod:
    """Half-open interval [starts_at, ends_at) with timezone-aware times."""

    starts_at: datetime
    ends_at: datetime

    def __post_init__(self) -> None:
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("BookingPeriod needs timezone-aware datetimes")
        if self.ends_at <= self.starts_at:
            raise BookingRejected("invalid_period")  # BK-05
        if self.ends_at - self.starts_at > MAX_BOOKING_DURATION:
            raise BookingRejected("booking_too_long")  # BK-04

    def overlaps(self, other: "BookingPeriod") -> bool:
        # BK-02: touching periods do not overlap.
        return self.starts_at < other.ends_at and other.starts_at < self.ends_at


@dataclass(frozen=True)
class Booking:
    id: UUID
    room_id: UUID
    member_id: UUID
    period: BookingPeriod
