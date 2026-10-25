"""@usecase UC-01 end to end against PostgreSQL."""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import psycopg
import pytest

from roombooking.adapters.persistence.postgres import PostgresBookingRepository, PostgresRoomRepository
from roombooking.application.book_room import BookRoom, BookRoomCommand
from roombooking.domain.errors import BookingRejected
from tests.fakes import FixedClock

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
ATLAS = UUID("7c0d3a52-0b1e-4c55-9a52-000000000001")  # seeded by 002_seed_rooms.sql


def make(conn: psycopg.Connection) -> BookRoom:
    return BookRoom(PostgresRoomRepository(conn), PostgresBookingRepository(conn), FixedClock(NOW))


def test_booking_is_stored(conn: psycopg.Connection) -> None:
    start = NOW + timedelta(days=1)
    booking_id = make(conn).execute(BookRoomCommand(uuid4(), ATLAS, start, start + timedelta(hours=1)))
    row = conn.execute("SELECT room_id, status FROM bookings WHERE id = %s", (booking_id,)).fetchone()
    assert row == (ATLAS, "active")


def test_unknown_room_is_rejected(conn: psycopg.Connection) -> None:
    """@rule RM-01"""
    start = NOW + timedelta(days=1)
    with pytest.raises(BookingRejected) as e:
        make(conn).execute(BookRoomCommand(uuid4(), uuid4(), start, start + timedelta(hours=1)))
    assert e.value.code == "room_not_found"


def test_fourth_upcoming_booking_is_rejected(conn: psycopg.Connection) -> None:
    """@rule BK-01"""
    member = uuid4()
    book_room = make(conn)
    for day in (1, 2, 3):
        start = NOW + timedelta(days=day)
        book_room.execute(BookRoomCommand(member, ATLAS, start, start + timedelta(hours=1)))
    start = NOW + timedelta(days=4)
    with pytest.raises(BookingRejected) as e:
        book_room.execute(BookRoomCommand(member, ATLAS, start, start + timedelta(hours=1)))
    assert e.value.code == "too_many_upcoming_bookings"
