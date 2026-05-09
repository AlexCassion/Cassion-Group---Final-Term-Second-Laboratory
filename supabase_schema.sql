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

CREATE INDEX IF NOT EXISTS idx_vote_queue_status ON vote_queue(status);

CREATE TABLE IF NOT EXISTS votes (
    id           BIGSERIAL PRIMARY KEY,
    doc_id       TEXT        UNIQUE NOT NULL,
    user_id      TEXT        NOT NULL,
    poll_id      TEXT        NOT NULL,
    choice       TEXT        NOT NULL CHECK (choice IN ('A', 'B', 'C')),
    edge_id      TEXT        DEFAULT 'unknown',
    timestamp    FLOAT8      NOT NULL,
    time_created FLOAT8      NOT NULL,
    processed_at FLOAT8,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_votes_poll ON votes(poll_id);
CREATE INDEX IF NOT EXISTS idx_votes_choice ON votes(choice);

CREATE OR REPLACE VIEW vote_tally AS
    SELECT poll_id, choice, COUNT(*) AS total
    FROM votes
    GROUP BY poll_id, choice
    ORDER BY poll_id, choice;
