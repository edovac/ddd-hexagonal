class CatalogError(Exception):
    pass


def add_book(conn, isbn, title, reference_only=False):
    isbn = isbn.replace("-", "")
    if len(isbn) not in (10, 13) or not isbn[:-1].isdigit():
        raise CatalogError("Invalid ISBN")
    row = conn.execute(
        "INSERT INTO books (isbn, title, reference_only) VALUES (%s, %s, %s) RETURNING id",
        (isbn, title, reference_only),
    ).fetchone()
    conn.commit()
    return row["id"]
