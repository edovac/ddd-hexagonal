from datetime import date, timedelta

from library.fees import late_fee

MAX_LOANS = 3
LOAN_DAYS = 21
CHILD_LOAN_DAYS = 14


class LoanError(Exception):
    pass


def open_loans(conn, member_id):
    return conn.execute(
        "SELECT * FROM loans WHERE member_id = %s AND returned_on IS NULL", (member_id,)
    ).fetchall()


def lend(conn, member_id, book_id, today=None):
    today = today or date.today()
    member = conn.execute("SELECT * FROM members WHERE id = %s", (member_id,)).fetchone()
    if member is None:
        raise LoanError("Unknown member")
    if member["suspended"]:
        raise LoanError("Member is suspended")
    book = conn.execute("SELECT * FROM books WHERE id = %s", (book_id,)).fetchone()
    if book["reference_only"]:
        raise LoanError("Reference books cannot be lent")
    if len(open_loans(conn, member_id)) >= MAX_LOANS:
        raise LoanError("Too many books on loan")
    days = CHILD_LOAN_DAYS if member["kind"] == "child" else LOAN_DAYS
    row = conn.execute(
        "INSERT INTO loans (member_id, book_id, lent_on, due_on) VALUES (%s, %s, %s, %s) RETURNING id",
        (member_id, book_id, today, today + timedelta(days=days)),
    ).fetchone()
    conn.commit()
    return row["id"]


def renew(conn, loan_id, today=None):
    today = today or date.today()
    loan = conn.execute("SELECT * FROM loans WHERE id = %s", (loan_id,)).fetchone()
    if loan["returned_on"] is not None:
        raise LoanError("Loan already returned")
    if loan["due_on"] < today:
        raise LoanError("Overdue loans cannot be renewed")
    conn.execute(
        "UPDATE loans SET renewals = renewals + 1, due_on = due_on + %s WHERE id = %s",
        (timedelta(days=LOAN_DAYS), loan_id),
    )
    conn.commit()


def give_back(conn, loan_id, today=None):
    today = today or date.today()
    loan = conn.execute("SELECT * FROM loans WHERE id = %s", (loan_id,)).fetchone()
    fee = late_fee((today - loan["due_on"]).days)
    conn.execute("UPDATE loans SET returned_on = %s WHERE id = %s", (today, loan_id))
    if fee:
        conn.execute("UPDATE members SET fees_owed = fees_owed + %s WHERE id = %s", (fee, loan["member_id"]))
        owed = conn.execute("SELECT fees_owed FROM members WHERE id = %s", (loan["member_id"],)).fetchone()
        if owed["fees_owed"] > 20:
            conn.execute("UPDATE members SET suspended = TRUE WHERE id = %s", (loan["member_id"],))
    conn.commit()
    return fee
