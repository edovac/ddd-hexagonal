import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"
DEFAULT_URL = "postgresql://postgres:test@localhost:5433/roombooking"


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    """A connection with the schema from the migrations, rolled back after each test."""
    with psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_URL)) as c:
        with c.transaction(force_rollback=True):
            for migration in sorted(MIGRATIONS.glob("*.sql")):
                c.execute(migration.read_text())
            yield c
