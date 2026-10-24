from datetime import datetime
from uuid import UUID

import psycopg
from psycopg import errors

from roombooking.domain.booking import Booking, BookingPeriod
from roombooking.domain.errors import BookingRejected


class PostgresBookingRepository:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def add(self, booking: Booking) -> None:
        try:
            # Savepoint, so a rejected insert leaves the caller's transaction usable.
            with self._conn.transaction():
                self._conn.execute(
                    "INSERT INTO bookings (id, room_id, member_id, starts_at, ends_at) VALUES (%s, %s, %s, %s, %s)",
                    (booking.id, booking.room_id, booking.member_id, booking.period.starts_at, booking.period.ends_at),
                )
        except errors.ExclusionViolation as e:
            raise BookingRejected("room_already_booked") from e  # BK-02, via bookings_no_overlap

    def count_upcoming_for_member(self, member_id: UUID, now: datetime) -> int:
        row = self._conn.execute(
            "SELECT count(*) FROM bookings WHERE member_id = %s AND status = 'active' AND starts_at > %s",
            (member_id, now),
        ).fetchone()
        return int(row[0]) if row else 0

    def active_periods_overlapping(self, room_id: UUID, period: BookingPeriod) -> list[BookingPeriod]:
        rows = self._conn.execute(
            "SELECT starts_at, ends_at FROM bookings"
            " WHERE room_id = %s AND status = 'active' AND starts_at < %s AND ends_at > %s",
            (room_id, period.ends_at, period.starts_at),
        ).fetchall()
        return [BookingPeriod(starts_at, ends_at) for starts_at, ends_at in rows]


class PostgresRoomRepository:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def exists(self, room_id: UUID) -> bool:
        return self._conn.execute("SELECT 1 FROM rooms WHERE id = %s", (room_id,)).fetchone() is not None
