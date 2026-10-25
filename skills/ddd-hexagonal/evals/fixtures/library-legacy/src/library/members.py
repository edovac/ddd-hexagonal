import re

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")


class MemberError(Exception):
    pass


def register(conn, name, email, kind="adult"):
    if not name.strip():
        raise MemberError("Name is required")
    if not EMAIL.match(email):
        raise MemberError("Invalid email")
    row = conn.execute(
        "INSERT INTO members (name, email, kind) VALUES (%s, %s, %s) RETURNING id", (name.strip(), email.lower(), kind)
    ).fetchone()
    conn.commit()
    return row["id"]


def pay_fees(conn, member_id, amount):
    if amount <= 0:
        raise MemberError("Amount must be positive")
    conn.execute("UPDATE members SET fees_owed = GREATEST(fees_owed - %s, 0) WHERE id = %s", (amount, member_id))
    owed = conn.execute("SELECT fees_owed FROM members WHERE id = %s", (member_id,)).fetchone()
    if owed["fees_owed"] == 0:
        conn.execute("UPDATE members SET suspended = FALSE WHERE id = %s", (member_id,))
    conn.commit()
