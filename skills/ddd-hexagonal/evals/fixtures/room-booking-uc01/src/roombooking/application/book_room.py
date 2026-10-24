from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from roombooking.application.ports import BookingRepository, Clock, RoomRepository
from roombooking.domain.booking import Booking, BookingPeriod
from roombooking.domain.booking_policy import check_new_booking
from roombooking.domain.errors import BookingRejected


@dataclass(frozen=True)
class BookRoomCommand:
    member_id: UUID
    room_id: UUID
    starts_at: datetime
    ends_at: datetime


class BookRoom:
    """UC-01 Book a room."""

    def __init__(
        self,
        rooms: RoomRepository,
        bookings: BookingRepository,
        clock: Clock,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings
        self._clock = clock
        self._new_id = new_id

    def execute(self, command: BookRoomCommand) -> UUID:
        if not self._rooms.exists(command.room_id):
            raise BookingRejected("room_not_found")  # RM-01
        period = BookingPeriod(command.starts_at, command.ends_at)
        now = self._clock.now()
        check_new_booking(
            period,
            now,
            self._bookings.count_upcoming_for_member(command.member_id, now),
            self._bookings.active_periods_overlapping(command.room_id, period),
        )
        booking = Booking(self._new_id(), command.room_id, command.member_id, period)
        self._bookings.add(booking)
        return booking.id
