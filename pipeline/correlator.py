"""The pipeline loop.

Claims events from Postgres, runs the rules over them, writes alerts back.
Runs until stopped. Every number it uses is an environment variable so the
behaviour can be changed without editing the file.
"""

import logging
import os
import signal
import sys
import time

from siemlib import db, enricher, rules
from siemlib.normalizer import normalize

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "100"))
WINDOW_SECONDS = int(os.environ.get("WINDOW_SECONDS", "300"))
DEDUP_SECONDS = int(os.environ.get("DEDUP_SECONDS", "300"))
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "1"))

log = logging.getLogger("correlator")

_running = True


def _stop(signum, frame):
    global _running
    _running = False
    log.info("signal %s received, finishing current pass", signum)


def emit(conn, alert):
    """Store one alert unless the same condition already fired recently.

    Returns True if it was written, False if it was suppressed.
    """
    if db.alert_recently_seen(conn, alert["dedup_key"], DEDUP_SECONDS):
        return False

    enrichment = enricher.enrich(alert["enrich_from"])
    db.insert_alert(
        conn,
        alert["name"],
        alert["severity"],
        alert["evidence"],
        enrichment,
        alert["dedup_key"],
    )
    log.info("alert: %s (severity %s)", alert["name"], alert["severity"])
    return True


def process_once(conn):
    """One pass. Returns how many alerts were written."""
    claimed = db.claim_events(conn, BATCH_SIZE)
    written = 0

    for row in claimed:
        event = normalize(row)
        for rule in rules.PER_EVENT_RULES:
            alert = rule(event)
            if alert and emit(conn, alert):
                written += 1

    if claimed:
        log.info("claimed %s event(s)", len(claimed))
        window = [normalize(row) for row in db.events_in_window(conn, WINDOW_SECONDS)]
        for rule in rules.WINDOWED_RULES:
            for alert in rule(window):
                if emit(conn, alert):
                    written += 1

    return written


def main():
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    conn = db.connect()
    db.init_schema(conn)
    log.info(
        "correlator up: batch=%s window=%ss dedup=%ss poll=%ss",
        BATCH_SIZE, WINDOW_SECONDS, DEDUP_SECONDS, POLL_SECONDS,
    )

    while _running:
        try:
            if process_once(conn) == 0:
                time.sleep(POLL_SECONDS)
        except Exception:
            # One bad pass should not kill the pipeline, but it must be visible.
            log.exception("pass failed, retrying")
            time.sleep(POLL_SECONDS)

    conn.close()
    log.info("correlator stopped")


if __name__ == "__main__":
    main()
