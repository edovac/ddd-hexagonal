CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE rooms (
    id   uuid PRIMARY KEY,
    name text NOT NULL UNIQUE
);

CREATE TABLE bookings (
    id        uuid PRIMARY KEY,
    room_id   uuid NOT NULL REFERENCES rooms (id),
    member_id uuid NOT NULL,
    starts_at timestamptz NOT NULL,
    ends_at   timestamptz NOT NULL,
    status    text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
    -- BK-05
    CONSTRAINT bookings_period_valid CHECK (ends_at > starts_at),
    -- BK-02, BK-08: active bookings of a room never overlap, also under concurrent requests; '[)' is half-open
    CONSTRAINT bookings_no_overlap EXCLUDE USING gist (
        room_id WITH =,
        tstzrange(starts_at, ends_at, '[)') WITH &&
    ) WHERE (status = 'active')
);

CREATE INDEX bookings_member_upcoming ON bookings (member_id, starts_at) WHERE status = 'active';
