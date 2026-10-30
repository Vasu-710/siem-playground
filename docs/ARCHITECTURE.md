# Architecture

How the parts fit together and why they are arranged this way. The README
covers running it.

## Services

Four containers, defined in `docker-compose.yml`.

| Service | Image or build | Job |
|---|---|---|
| `db` | `postgres:16` | Stores events and alerts |
| `collector` | `infra/Dockerfile.api` | HTTP in, alerts out |
| `pipeline` | `infra/Dockerfile.pipeline` | Detection loop |
| `ui` | `infra/Dockerfile.ui` | React dashboard |

`collector` and `pipeline` both wait on the database's healthcheck rather than
just on the container starting, because Postgres accepts connections several
seconds after the process exists.

## Shared code

`siemlib/` is imported by both Python services. They have to agree on the
schema and on what a normalised event looks like, so that agreement lives in
one place and both Dockerfiles copy it in.

```
siemlib/
  schema.sql      the two tables and their indexes
  db.py           every SQL statement in the project
  normalizer.py   raw event  ->  canonical fields
  rules.py        detection rules
  enricher.py     indicator lookup
```

## The data model

**`events`** is a queue with history. `processed_at` is NULL until a pipeline
pass claims the row, and the partial index `events_unprocessed_idx` covers only
those rows, so finding work stays cheap as the table grows.

**`alerts`** holds what fired. `evidence` and `enrichment` are JSONB. The
`dedup_key` column is what stops a standing condition from raising a fresh
alert on every pass.

Both tables keep everything. Nothing in this project deletes rows.

## Claiming, not reading

This is the part worth understanding, because the first version got it wrong.

The pipeline does not read the events table and then mark rows done. It does
both in one statement:

```sql
UPDATE events
   SET processed_at = now()
 WHERE id IN (
       SELECT id FROM events
        WHERE processed_at IS NULL
        ORDER BY id LIMIT %s
        FOR UPDATE SKIP LOCKED
 )
RETURNING id, ts, source, event_type, payload
```

The rows come back already claimed. Nothing can arrive, be missed and then be
destroyed in between, which is exactly what the old file based queue did when
it truncated the file after reading it.

`SKIP LOCKED` means a second pipeline process would take different rows instead
of blocking or double-processing. Only one is run today, but the statement does
not have to change to add another.

## Normalisation

Sources disagree about field names. `normalizer.normalize()` is the only place
that has to care, and every rule downstream can assume these keys exist:

`ts`, `source`, `type`, `payload`, `host`, `user`, `ip`, `domain`

Two decisions in there are deliberate. Timestamps are always parsed to
timezone-aware UTC, and an unparseable one falls back to now rather than
raising, because a single sender with a broken clock format should not stop
ingestion. And `user` reads `user` or `username`, since the demo dataset sends
one and the rules want the other.

## Rules

A rule is a plain function. No database connection, no clock, no file access.
Per-event rules take one event, windowed rules take a list and the caller
decides what the window is.

Every rule returns the same shape:

```python
{
  "name":        str,   # what the alert is called
  "severity":    int,   # 1 to 10, enforced by a CHECK constraint
  "evidence":    dict,  # stored as JSONB, must be JSON safe
  "dedup_key":   str,   # identity of the condition, not of the alert
  "enrich_from": dict,  # the event whose indicators get looked up
}
```

Keeping rules pure is what makes them testable against a fixed list of events,
with no database and no waiting. `tests/test_rules.py` is the result.

## A pass

`pipeline.correlator.process_once()`:

1. Claim up to `BATCH_SIZE` unprocessed events.
2. Run every per-event rule over each one.
3. If anything was claimed, load the last `WINDOW_SECONDS` of events, processed
   or not, and run every windowed rule over that.
4. For each alert, skip it if the same `dedup_key` fired within
   `DEDUP_SECONDS`, otherwise enrich and store it.

Step 3 reads the whole window rather than just the claimed batch, because a
windowed rule needs the window. If it only saw this pass's rows it would be
counting whatever happened to arrive in the last second, which is what the old
version did.

An exception in a pass is logged and the loop continues. One malformed event
should not take the pipeline down, but it must be visible in the logs.

## The collector

Deliberately thin. It writes events and reads alerts, and it makes no decisions
about either. Detection logic lives in one place.

Handlers are synchronous because the connection pool is a threaded pool, so
FastAPI runs them in worker threads instead of blocking the event loop.

`/health` checks the database. A collector that cannot store an event is not
healthy however alive the process is.

Allowed origins are listed explicitly and set per deployment. Wildcard origins
combined with credentials is a configuration browsers reject anyway.

## The dashboard

`ui/src/App.js` polls `/api/alerts` every three seconds. Polling, not
websockets, because three seconds is fine for this and a websocket would be a
second thing to get right.

Severity thresholds live in `ui/src/severity.js` rather than inside the
component, so they can be tested on their own and so anything else added later
agrees on what HIGH means.

## Testing

| File | Needs a database |
|---|---|
| `test_normalizer.py` | no |
| `test_enricher.py` | no |
| `test_rules.py` | no |
| `test_db.py` | yes |
| `test_pipeline.py` | yes |
| `test_api.py` | yes |

The database tests run against a real Postgres and skip when
`TEST_DATABASE_URL` is unset. They are testing SQL, and a mocked database would
only prove the mock behaves like the mock. CI starts a Postgres service
container so they run there.

## What would need to change for this to be real

- Authentication on both the ingest and the read side. There is none.
- Retention. Nothing is ever deleted.
- Alert routing. Alerts stop at the database.
- Real threat feeds instead of a dict.
- More than two rules.
