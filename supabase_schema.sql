CREATE TABLE IF NOT EXISTS vote_queue (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT        NOT NULL,
    poll_id     TEXT        NOT NULL,
    choice      TEXT        NOT NULL CHECK (choice IN ('A', 'B', 'C')),
    edge_id     TEXT        DEFAULT 'unknown',
    timestamp   FLOAT8      NOT NULL,
    time_created FLOAT8     NOT NULL,
    status      TEXT        DEFAULT 'pending' CHECK (status IN ('pending', 'processed')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
