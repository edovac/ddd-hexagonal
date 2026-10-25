# Library lending desk

Flask app used at the front desk: register members, add books, lend, renew and return.

    docker compose up -d db
    psql postgresql://postgres:test@localhost:5433/library -f migrations/001_init.sql
    DATABASE_URL=postgresql://postgres:test@localhost:5433/library uv run flask --app library.web run

Tests: `uv run pytest`.
