"""Contract tests: the in-memory fake and the PostgreSQL repository behave the same."""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import psycopg
import pytest

from roombooking.adapters.persistence.postgres import PostgresBookingRepository
from roombooking.application.ports import BookingRepository
from roombooking.domain.booking import Booking, BookingPeriod
from roombooking.domain.errors import BookingRejected
from tests.fakes import InMemoryBookingRepository

START = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


def insert_room(conn: psycopg.Connection) -> UUID:
    room_id = uuid4()
    conn.execute("INSERT INTO rooms (id, name) VALUES (%s, %s)", (room_id, f"room-{room_id}"))
    return room_id


@pytest.fixture(params=["in_memory", "postgres"])
def repo_and_room(request: pytest.FixtureRequest) -> tuple[BookingRepository, UUID]:
    if request.param == "in_memory":
        return InMemoryBookingRepository(), uuid4()
    conn: psycopg.Connection = request.getfixturevalue("conn")
    return PostgresBookingRepository(conn), insert_room(conn)


def booking(room: UUID, start: datetime, hours: int = 1, member: UUID | None = None) -> Booking:
    return Booking(uuid4(), room, member or uuid4(), BookingPeriod(start, start + timedelta(hours=hours)))


def test_counts_only_bookings_that_start_after_now(repo_and_room: tuple[BookingRepository, UUID]) -> None:
    """@rule BK-01"""
    repo, room = repo_and_room
    member = uuid4()
    repo.add(booking(room, START, member=member))
    repo.add(booking(room, START + timedelta(days=1), member=member))
    assert repo.count_upcoming_for_member(member, START) == 1
    assert repo.count_upcoming_for_member(member, START - timedelta(minutes=1)) == 2


def test_touching_periods_are_not_returned_as_overlapping(repo_and_room: tuple[BookingRepository, UUID]) -> None:
    """@rule BK-02"""
    repo, room = repo_and_room
    repo.add(booking(room, START))
    after = BookingPeriod(START + timedelta(hours=1), START + timedelta(hours=2))
    during = BookingPeriod(START + timedelta(minutes=30), START + timedelta(hours=2))
    assert repo.active_periods_overlapping(room, after) == []
    assert len(repo.active_periods_overlapping(room, during)) == 1


def test_adding_an_overlapping_booking_is_rejected(repo_and_room: tuple[BookingRepository, UUID]) -> None:
    """@rule BK-02 - the PostgreSQL side is guaranteed by bookings_no_overlap, also under concurrency."""
    repo, room = repo_and_room
    repo.add(booking(room, START, hours=2))
    with pytest.raises(BookingRejected) as e:
        repo.add(booking(room, START + timedelta(hours=1)))
    assert e.value.code == "room_already_booked"
