"""Characterization tests for the Lending area (docs/business-rules.md, LN).

They pin what the code does today through its existing seams: the functions in
library.loans and the Flask routes, against the real PostgreSQL.
"""

from datetime import date, timedelta

import psycopg
import pytest

from library import loans

DAY = date(2026, 3, 2)


def open_loan_count(conn, member_id):
    return len(loans.open_loans(conn, member_id))


# --- UC-01 Lend a book -------------------------------------------------------


def test_unknown_member_cannot_borrow(conn, make_book):
    """@rule LN-01 @usecase UC-01"""
    book = make_book()
    with pytest.raises(loans.LoanError, match="Unknown member"):
        loans.lend(conn, 999, book, today=DAY)


def test_suspended_member_cannot_borrow(conn, make_member, make_book):
    """@rule LN-02 @usecase UC-01"""
    member = make_member(suspended=True)
    with pytest.raises(loans.LoanError, match="Member is suspended"):
        loans.lend(conn, member, make_book(), today=DAY)
    assert open_loan_count(conn, member) == 0


def test_book_not_in_catalogue_cannot_be_lent(conn, make_member):
    """@rule LN-03 @usecase UC-01

    Today this fails with a TypeError (HTTP 500), not a LoanError: see the error-code gap."""
    member = make_member()
    with pytest.raises(Exception):
        loans.lend(conn, member, 999, today=DAY)
    conn.rollback()
    assert open_loan_count(conn, member) == 0


def test_reference_only_book_cannot_be_lent(conn, make_member, make_book):
    """@rule LN-04 @usecase UC-01"""
    member = make_member()
    with pytest.raises(loans.LoanError, match="Reference books cannot be lent"):
        loans.lend(conn, member, make_book(reference_only=True), today=DAY)
    assert open_loan_count(conn, member) == 0


def test_member_can_have_three_open_loans_and_not_a_fourth(conn, make_member, make_book):
    """@rule LN-05 @usecase UC-01"""
    member = make_member()
    for _ in range(3):
        loans.lend(conn, member, make_book(), today=DAY)
    with pytest.raises(loans.LoanError, match="Too many books on loan"):
        loans.lend(conn, member, make_book(), today=DAY)
    assert open_loan_count(conn, member) == 3


def test_returned_loans_do_not_count_toward_the_limit(conn, make_member, make_book):
    """@rule LN-05 @usecase UC-01"""
    member = make_member()
    first = loans.lend(conn, member, make_book(), today=DAY)
    for _ in range(2):
        loans.lend(conn, member, make_book(), today=DAY)
    loans.give_back(conn, first, today=DAY)
    loans.lend(conn, member, make_book(), today=DAY)
    assert open_loan_count(conn, member) == 3


def test_desk_route_rejects_the_fourth_loan_despite_its_limit_of_five(client, make_member, make_book):
    """@rule LN-05 @usecase UC-01

    web.py checks 5 open loans, loans.py checks 3; through the route the 3 wins."""
    member = make_member()
    for _ in range(3):
        assert client.post("/loans", json={"member_id": member, "book_id": make_book()}).status_code == 201
    response = client.post("/loans", json={"member_id": member, "book_id": make_book()})
    assert response.status_code == 409
    assert response.get_json() == {"error": "Too many books on loan"}


def test_book_already_on_loan_cannot_be_lent_again(conn, make_member, make_book):
    """@rule LN-06 @usecase UC-01

    Only the unique index one_open_loan_per_book enforces it today (HTTP 500)."""
    book = make_book()
    loans.lend(conn, make_member(), book, today=DAY)
    other = make_member()
    with pytest.raises(psycopg.errors.UniqueViolation):
        loans.lend(conn, other, book, today=DAY)
    conn.rollback()
    assert open_loan_count(conn, other) == 0


def test_returned_book_can_be_lent_again(conn, make_member, make_book):
    """@rule LN-06 @usecase UC-01"""
    book = make_book()
    first = loans.lend(conn, make_member(), book, today=DAY)
    loans.give_back(conn, first, today=DAY)
    loans.lend(conn, make_member(), book, today=DAY)


@pytest.mark.parametrize(("kind", "days"), [("adult", 21), ("staff", 21), ("child", 14)])
def test_due_date_depends_on_member_kind(conn, make_member, make_book, kind, days):
    """@rule LN-07 @usecase UC-01"""
    loan_id = loans.lend(conn, make_member(kind=kind), make_book(), today=DAY)
    loan = conn.execute("SELECT lent_on, due_on FROM loans WHERE id = %s", (loan_id,)).fetchone()
    assert loan["lent_on"] == DAY
    assert loan["due_on"] == DAY + timedelta(days=days)


# --- UC-02 Renew a loan ------------------------------------------------------


def lend_one(conn, make_member, make_book, kind="adult"):
    return loans.lend(conn, make_member(kind=kind), make_book(), today=DAY)


def due_on(conn, loan_id):
    return conn.execute("SELECT due_on FROM loans WHERE id = %s", (loan_id,)).fetchone()["due_on"]


def test_returned_loan_cannot_be_renewed(conn, make_member, make_book):
    """@rule LN-08 @usecase UC-02"""
    loan_id = lend_one(conn, make_member, make_book)
    loans.give_back(conn, loan_id, today=DAY)
    with pytest.raises(loans.LoanError, match="Loan already returned"):
        loans.renew(conn, loan_id, today=DAY)


def test_loan_can_be_renewed_on_its_due_date(conn, make_member, make_book):
    """@rule LN-09 @usecase UC-02"""
    loan_id = lend_one(conn, make_member, make_book)
    due = due_on(conn, loan_id)
    loans.renew(conn, loan_id, today=due)
    assert due_on(conn, loan_id) == due + timedelta(days=21)


def test_overdue_loan_cannot_be_renewed(conn, make_member, make_book):
    """@rule LN-09 @usecase UC-02"""
    loan_id = lend_one(conn, make_member, make_book)
    due = due_on(conn, loan_id)
    with pytest.raises(loans.LoanError, match="Overdue loans cannot be renewed"):
        loans.renew(conn, loan_id, today=due + timedelta(days=1))
    assert due_on(conn, loan_id) == due


@pytest.mark.parametrize("kind", ["adult", "staff"])
def test_renewal_adds_21_days_to_the_current_due_date(conn, make_member, make_book, kind):
    """@rule LN-10 @usecase UC-02

    Renewed early, the new due date counts from the old due date, not from today."""
    loan_id = lend_one(conn, make_member, make_book, kind=kind)
    due = due_on(conn, loan_id)
    loans.renew(conn, loan_id, today=DAY + timedelta(days=1))
    assert due_on(conn, loan_id) == due + timedelta(days=21)


def test_loan_can_be_renewed_twice_but_not_a_third_time(conn, make_member, make_book):
    """@rule LN-11 @usecase UC-02

    Only the CHECK (renewals <= 2) enforces it today (HTTP 500)."""
    loan_id = lend_one(conn, make_member, make_book)
    loans.renew(conn, loan_id, today=DAY)
    loans.renew(conn, loan_id, today=DAY)
    due = due_on(conn, loan_id)
    with pytest.raises(psycopg.errors.CheckViolation):
        loans.renew(conn, loan_id, today=DAY)
    conn.rollback()
    assert due_on(conn, loan_id) == due


# --- UC-03 Return a book -----------------------------------------------------


def test_return_records_the_return_date(conn, make_member, make_book):
    """@usecase UC-03"""
    loan_id = lend_one(conn, make_member, make_book)
    loans.give_back(conn, loan_id, today=DAY + timedelta(days=3))
    row = conn.execute("SELECT returned_on FROM loans WHERE id = %s", (loan_id,)).fetchone()
    assert row["returned_on"] == DAY + timedelta(days=3)


@pytest.mark.xfail(
    strict=True,
    reason="LN-12: code accepts a second return and charges the late fee again; see open point",
)
def test_returned_loan_cannot_be_returned_again(conn, make_member, make_book):
    """@rule LN-12 @usecase UC-03"""
    member = make_member()
    loan_id = loans.lend(conn, member, make_book(), today=DAY)
    first_return = DAY + timedelta(days=25)
    loans.give_back(conn, loan_id, today=first_return)
    with pytest.raises(loans.LoanError):
        loans.give_back(conn, loan_id, today=first_return + timedelta(days=10))
    row = conn.execute("SELECT returned_on FROM loans WHERE id = %s", (loan_id,)).fetchone()
    assert row["returned_on"] == first_return
