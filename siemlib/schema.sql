-- Events arrive from the collector and are claimed by the pipeline.
-- processed_at is NULL until a pipeline pass takes the row.
CREATE TABLE IF NOT EXISTS events (
    id           BIGSERIAL   PRIMARY KEY,
    received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts           TIMESTAMPTZ NOT NULL,
    source       TEXT        NOT NULL,
    event_type   TEXT        NOT NULL,
    payload      JSONB       NOT NULL,
    processed_at TIMESTAMPTZ
);

-- Partial index: the pipeline only ever looks for unprocessed rows.
CREATE INDEX IF NOT EXISTS events_unprocessed_idx
    ON events (id) WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS events_ts_idx ON events (ts);

CREATE TABLE IF NOT EXISTS alerts (
    id         BIGSERIAL   PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    name       TEXT        NOT NULL,
    severity   INT         NOT NULL CHECK (severity BETWEEN 1 AND 10),
    evidence   JSONB       NOT NULL,
    enrichment JSONB       NOT NULL DEFAULT '{}'::jsonb,
    dedup_key  TEXT
);

CREATE INDEX IF NOT EXISTS alerts_created_idx ON alerts (created_at DESC);
CREATE INDEX IF NOT EXISTS alerts_dedup_idx ON alerts (dedup_key, created_at DESC);
