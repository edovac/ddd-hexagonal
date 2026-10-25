import psycopg

from roombooking.adapters.clock import SystemClock
from roombooking.adapters.persistence.postgres import PostgresBookingRepository, PostgresRoomRepository
from roombooking.application.book_room import BookRoom


def book_room(conn: psycopg.Connection) -> BookRoom:
    return BookRoom(PostgresRoomRepository(conn), PostgresBookingRepository(conn), SystemClock())
