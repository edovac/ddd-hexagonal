from datetime import UTC, datetime, timedelta

import pytest

from roombooking.domain.booking import BookingPeriod
from roombooking.domain.errors import BookingRejected

START = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


def test_end_before_start_is_rejected() -> None:
    """@rule BK-05"""
    with pytest.raises(BookingRejected) as e:
        BookingPeriod(START, START - timedelta(minutes=30))
    assert e.value.code == "invalid_period"


def test_zero_length_is_rejected() -> None:
    """@rule BK-05"""
    with pytest.raises(BookingRejected) as e:
        BookingPeriod(START, START)
    assert e.value.code == "invalid_period"


def test_exactly_eight_hours_is_allowed() -> None:
    """@rule BK-04"""
    assert BookingPeriod(START, START + timedelta(hours=8)).ends_at == START + timedelta(hours=8)


def test_longer_than_eight_hours_is_rejected() -> None:
    """@rule BK-04"""
    with pytest.raises(BookingRejected) as e:
        BookingPeriod(START, START + timedelta(hours=8, minutes=1))
    assert e.value.code == "booking_too_long"


def test_touching_periods_do_not_overlap() -> None:
    """@rule BK-02"""
    first = BookingPeriod(START, START + timedelta(hours=1))
    second = BookingPeriod(START + timedelta(hours=1), START + timedelta(hours=2))
    assert not first.overlaps(second)
    assert not second.overlaps(first)


def test_naive_datetimes_are_refused() -> None:
    with pytest.raises(ValueError):
        BookingPeriod(datetime(2026, 11, 2, 9, 0), datetime(2026, 11, 2, 10, 0))
