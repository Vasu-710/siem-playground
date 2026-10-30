"""Postgres access.

Events used to sit in a JSONL file that the pipeline truncated after every
pass. Anything the collector appended between the read and the truncate was
lost without a trace. Claiming rows inside the database instead means an event
is handed to exactly one pass and is never thrown away.
"""

import os
import pathlib

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

DEFAULT_URL = "postgresql://siem:siem_pass@db:5432/siemdb"
SCHEMA_PATH = pathlib.Path(__file__).with_name("schema.sql")


def database_url():
    url = os.environ.get("DATABASE_URL", DEFAULT_URL)
    # Compose historically passed postgres://, psycopg wants postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def connect(timeout=60.0):
    """A single connection, waiting for Postgres to come up.

    Compose starts the database and the services at the same time, so the first
    attempts fail while Postgres is still starting.
    """
    return psycopg.connect(
        database_url(), row_factory=dict_row, autocommit=True, connect_timeout=int(timeout)
    )


def make_pool(min_size=1, max_size=4, timeout=60.0):
    """A pool for the API, which serves requests from several threads."""
    pool = ConnectionPool(
        database_url(),
        min_size=min_size,
        max_size=max_size,
        kwargs={"row_factory": dict_row, "autocommit": True},
        open=False,
    )
    pool.open(wait=True, timeout=timeout)
    return pool


def init_schema(conn):
    conn.execute(SCHEMA_PATH.read_text())


def insert_event(conn, ts, source, event_type, payload):
    row = conn.execute(
        "INSERT INTO events (ts, source, event_type, payload)"
        " VALUES (%s, %s, %s, %s) RETURNING id",
        (ts, source, event_type, Jsonb(payload)),
    ).fetchone()
    return row["id"]


CLAIM_SQL = """
UPDATE events
   SET processed_at = now()
 WHERE id IN (
       SELECT id
         FROM events
        WHERE processed_at IS NULL
        ORDER BY id
        LIMIT %s
        FOR UPDATE SKIP LOCKED
 )
RETURNING id, ts, source, event_type, payload
"""


def claim_events(conn, limit):
    """Take up to `limit` unprocessed events and mark them taken, atomically.

    FOR UPDATE SKIP LOCKED means a second pipeline process picks different rows
    rather than blocking or double-processing.
    """
    return conn.execute(CLAIM_SQL, (limit,)).fetchall()


def events_in_window(conn, seconds):
    """Every event with a timestamp inside the last `seconds`, processed or not.

    Windowed rules need the whole window, not just the rows this pass claimed.
    """
    return conn.execute(
        "SELECT id, ts, source, event_type, payload FROM events"
        " WHERE ts > now() - make_interval(secs => %s) ORDER BY ts",
        (seconds,),
    ).fetchall()


def alert_recently_seen(conn, dedup_key, seconds):
    if not dedup_key:
        return False
    row = conn.execute(
        "SELECT 1 FROM alerts WHERE dedup_key = %s"
        " AND created_at > now() - make_interval(secs => %s) LIMIT 1",
        (dedup_key, seconds),
    ).fetchone()
    return row is not None


def insert_alert(conn, name, severity, evidence, enrichment, dedup_key):
    row = conn.execute(
        "INSERT INTO alerts (name, severity, evidence, enrichment, dedup_key)"
        " VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (name, severity, Jsonb(evidence), Jsonb(enrichment), dedup_key),
    ).fetchone()
    return row["id"]


def list_alerts(conn, limit=100):
    rows = conn.execute(
        "SELECT id, created_at, name, severity, evidence, enrichment"
        " FROM alerts ORDER BY created_at DESC, id DESC LIMIT %s",
        (limit,),
    ).fetchall()
    for row in rows:
        row["created_at"] = row["created_at"].isoformat()
    return rows


def counts(conn):
    return conn.execute(
        "SELECT (SELECT count(*) FROM events) AS events,"
        " (SELECT count(*) FROM events WHERE processed_at IS NULL) AS pending,"
        " (SELECT count(*) FROM alerts) AS alerts"
    ).fetchone()
