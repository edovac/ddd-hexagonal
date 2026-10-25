from datetime import datetime
from uuid import UUID

from roombooking.domain.booking import Booking, BookingPeriod
from roombooking.domain.errors import BookingRejected


class InMemoryBookingRepository:
    def __init__(self) -> None:
        self.bookings: list[Booking] = []

    def add(self, booking: Booking) -> None:
        if self.active_periods_overlapping(booking.room_id, booking.period):
            raise BookingRejected("room_already_booked")
        self.bookings.append(booking)

    def count_upcoming_for_member(self, member_id: UUID, now: datetime) -> int:
        return sum(1 for b in self.bookings if b.member_id == member_id and b.period.starts_at > now)

    def active_periods_overlapping(self, room_id: UUID, period: BookingPeriod) -> list[BookingPeriod]:
        return [b.period for b in self.bookings if b.room_id == room_id and b.period.overlaps(period)]


class InMemoryRoomRepository:
    def __init__(self, *room_ids: UUID) -> None:
        self.room_ids = set(room_ids)

    def exists(self, room_id: UUID) -> bool:
        return room_id in self.room_ids


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current
