CREATE TABLE IF NOT EXISTS vote_queue (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT        NOT NULL,
    poll_id     TEXT        NOT NULL,
