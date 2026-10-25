"""Integration fixtures: the real PostgreSQL named by DATABASE_URL.

Each test session creates its own schema, applies migrations/*.sql in order and drops
the schema at the end. The code under test commits, so tables are emptied after each
test instead of rolling back.
"""

import os
import uuid
from pathlib import Path
from urllib.parse import quote

import psycopg
import pytest
from psycopg.rows import dict_row

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"


def _with_search_path(url: str, schema: str) -> str:
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}options={quote(f'-csearch_path={schema}')}"


@pytest.fixture(scope="session")
def database_url():
    base = os.environ.get("DATABASE_URL")
    if not base:
        pytest.skip("integration tests need DATABASE_URL pointing at PostgreSQL")
    schema = f"test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(f"CREATE SCHEMA {schema}")
    url = _with_search_path(base, schema)
    with psycopg.connect(url) as conn:
        for migration in sorted(MIGRATIONS.glob("*.sql")):
            conn.execute(migration.read_text())
        conn.commit()
    yield url
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(f"DROP SCHEMA {schema} CASCADE")


@pytest.fixture
def conn(database_url, monkeypatch):
    """A connection like library.db.connect() gives, on the test schema."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    connection = psycopg.connect(database_url, row_factory=dict_row)
    yield connection
    connection.rollback()
    connection.execute("TRUNCATE loans, books, members RESTART IDENTITY CASCADE")
    connection.commit()
    connection.close()


@pytest.fixture
def client(conn):
    from library.web import app

    return app.test_client()


@pytest.fixture
def make_member(conn):
    def make(kind="adult", suspended=False, fees_owed=0):
        row = conn.execute(
            "INSERT INTO members (name, email, kind, suspended, fees_owed)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING id",
            ("Test Member", f"{uuid.uuid4().hex[:8]}@example.org", kind, suspended, fees_owed),
        ).fetchone()
        conn.commit()
        return row["id"]

    return make


@pytest.fixture
def make_book(conn):
    def make(reference_only=False):
        row = conn.execute(
            "INSERT INTO books (isbn, title, reference_only) VALUES (%s, %s, %s) RETURNING id",
            (uuid.uuid4().hex[:13], "Test Book", reference_only),
        ).fetchone()
        conn.commit()
        return row["id"]

    return make
