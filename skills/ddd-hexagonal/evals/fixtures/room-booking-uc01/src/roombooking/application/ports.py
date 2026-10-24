from datetime import datetime
from typing import Protocol
from uuid import UUID

from roombooking.domain.booking import Booking, BookingPeriod


class BookingRepository(Protocol):
    def add(self, booking: Booking) -> None:
        """Save a new active booking; raise BookingRejected("room_already_booked") on overlap (BK-02)."""
        ...

    def count_upcoming_for_member(self, member_id: UUID, now: datetime) -> int: ...

    def active_periods_overlapping(self, room_id: UUID, period: BookingPeriod) -> list[BookingPeriod]: ...


class RoomRepository(Protocol):
    def exists(self, room_id: UUID) -> bool: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
