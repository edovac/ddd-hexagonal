CREATE TABLE members (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    kind        TEXT NOT NULL DEFAULT 'adult' CHECK (kind IN ('adult', 'child', 'staff')),
    suspended   BOOLEAN NOT NULL DEFAULT FALSE,
    fees_owed   NUMERIC(8, 2) NOT NULL DEFAULT 0
);

CREATE TABLE books (
    id          SERIAL PRIMARY KEY,
    isbn        TEXT NOT NULL UNIQUE,
    title       TEXT NOT NULL,
    reference_only BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE loans (
    id          SERIAL PRIMARY KEY,
    member_id   INTEGER NOT NULL REFERENCES members(id),
    book_id     INTEGER NOT NULL REFERENCES books(id),
    lent_on     DATE NOT NULL,
    due_on      DATE NOT NULL,
    renewals    INTEGER NOT NULL DEFAULT 0 CHECK (renewals <= 2),
    returned_on DATE
);

-- a book can be out on one loan at a time
CREATE UNIQUE INDEX one_open_loan_per_book ON loans (book_id) WHERE returned_on IS NULL;
