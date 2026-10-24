"""@usecase UC-01"""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from roombooking.application.book_room import BookRoom, BookRoomCommand
from roombooking.domain.errors import BookingRejected
from tests.fakes import FixedClock, InMemoryBookingRepository, InMemoryRoomRepository

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
ROOM = uuid4()
OTHER_ROOM = uuid4()
MEMBER = uuid4()


@pytest.fixture
def bookings() -> InMemoryBookingRepository:
    return InMemoryBookingRepository()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def book_room(bookings: InMemoryBookingRepository, clock: FixedClock) -> BookRoom:
    return BookRoom(InMemoryRoomRepository(ROOM, OTHER_ROOM), bookings, clock)


def command(start_in_hours: float, hours: float = 1, room: UUID = ROOM, member: UUID = MEMBER) -> BookRoomCommand:
    start = NOW + timedelta(hours=start_in_hours)
    return BookRoomCommand(member, room, start, start + timedelta(hours=hours))


def rejected_code(book_room: BookRoom, cmd: BookRoomCommand) -> str:
    with pytest.raises(BookingRejected) as e:
        book_room.execute(cmd)
    return e.value.code


def test_booking_is_saved(book_room: BookRoom, bookings: InMemoryBookingRepository) -> None:
    booking_id = book_room.execute(command(24))
    assert [b.id for b in bookings.bookings] == [booking_id]


def test_unknown_room_is_rejected(book_room: BookRoom, bookings: InMemoryBookingRepository) -> None:
    """@rule RM-01"""
    assert rejected_code(book_room, command(24, room=uuid4())) == "room_not_found"
    assert bookings.bookings == []


def test_third_upcoming_booking_is_allowed_fourth_is_rejected(book_room: BookRoom) -> None:
    """@rule BK-01"""
    for day in (1, 2, 3):
        book_room.execute(command(24 * day))
    assert rejected_code(book_room, command(24 * 4)) == "too_many_upcoming_bookings"


def test_past_bookings_do_not_count_as_upcoming(book_room: BookRoom, clock: FixedClock) -> None:
    """@rule BK-01"""
    for day in (1, 2, 3):
        book_room.execute(command(24 * day))
    clock.current = NOW + timedelta(days=1, hours=2)  # the first booking is over
    book_room.execute(command(24 * 4))


def test_overlapping_booking_of_same_room_is_rejected(book_room: BookRoom) -> None:
    """@rule BK-02"""
    book_room.execute(command(24, hours=2))
    assert rejected_code(book_room, command(25, member=uuid4())) == "room_already_booked"


def test_booking_that_starts_when_another_ends_is_allowed(book_room: BookRoom) -> None:
    """@rule BK-02"""
    book_room.execute(command(24, hours=1))
    book_room.execute(command(25, hours=1, member=uuid4()))


def test_same_time_in_another_room_is_allowed(book_room: BookRoom) -> None:
    """@rule BK-02"""
    book_room.execute(command(24))
    book_room.execute(command(24, room=OTHER_ROOM, member=uuid4()))


def test_booking_starting_now_is_rejected(book_room: BookRoom) -> None:
    """@rule BK-03"""
    assert rejected_code(book_room, command(0)) == "booking_in_past"


def test_booking_in_the_past_is_rejected(book_room: BookRoom) -> None:
    """@rule BK-03"""
    assert rejected_code(book_room, command(-2)) == "booking_in_past"


def test_too_long_booking_is_rejected(book_room: BookRoom) -> None:
    """@rule BK-04"""
    assert rejected_code(book_room, command(24, hours=9)) == "booking_too_long"


def test_period_ending_before_start_is_rejected(book_room: BookRoom) -> None:
    """@rule BK-05"""
    assert rejected_code(book_room, command(24, hours=-1)) == "invalid_period"
