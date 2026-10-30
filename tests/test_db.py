"""Tests for the SQL itself, against a real Postgres."""

from datetime import datetime, timedelta, timezone

import pytest

from siemlib import db

BASE = datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)


def add(conn, event_type="link_clicked", seconds=0, payload=None):
    return db.insert_event(
        conn, BASE + timedelta(seconds=seconds), "redteam", event_type, payload or {}
    )


class TestInsertAndClaim:
    def test_an_inserted_event_can_be_claimed_once(self, conn):
        add(conn)
        assert len(db.claim_events(conn, 10)) == 1
        assert db.claim_events(conn, 10) == []

    def test_claiming_respects_the_limit(self, conn):
        for i in range(5):
            add(conn, seconds=i)
        assert len(db.claim_events(conn, 2)) == 2
        assert len(db.claim_events(conn, 10)) == 3

    def test_claimed_rows_keep_their_payload(self, conn):
        add(conn, payload={"campaign_id": "camp1", "ip": "1.2.3.4"})
        row = db.claim_events(conn, 1)[0]
        assert row["payload"]["campaign_id"] == "camp1"

    def test_an_event_inserted_during_a_pass_is_not_lost(self, conn):
        """The bug this replaced: the old pipeline truncated the queue file
        after reading it, so anything written in between vanished."""
        add(conn, seconds=1)
        db.claim_events(conn, 10)
        add(conn, seconds=2)
        assert len(db.claim_events(conn, 10)) == 1


class TestWindow:
    def test_window_includes_already_processed_events(self, conn):
        add(conn, seconds=0)
        db.claim_events(conn, 10)
        in_window = db.events_in_window(conn, 10 ** 9)
        assert len(in_window) == 1

    def test_window_excludes_events_outside_it(self, conn):
        db.insert_event(
            conn, datetime.now(timezone.utc) - timedelta(hours=2), "s", "link_clicked", {}
        )
        db.insert_event(conn, datetime.now(timezone.utc), "s", "link_clicked", {})
        assert len(db.events_in_window(conn, 300)) == 1


class TestAlerts:
    def test_insert_and_list(self, conn):
        db.insert_alert(conn, "Test", 7, {"a": 1}, {"b": 2}, "k1")
        alerts = db.list_alerts(conn)
        assert alerts[0]["name"] == "Test"
        assert alerts[0]["evidence"] == {"a": 1}
        assert isinstance(alerts[0]["created_at"], str)

    def test_severity_outside_the_range_is_rejected(self, conn):
        with pytest.raises(Exception):
            db.insert_alert(conn, "Bad", 99, {}, {}, "k")

    def test_dedup_sees_a_recent_alert(self, conn):
        db.insert_alert(conn, "Test", 5, {}, {}, "k1")
        assert db.alert_recently_seen(conn, "k1", 300) is True

    def test_dedup_ignores_an_old_alert(self, conn):
        db.insert_alert(conn, "Test", 5, {}, {}, "k1")
        conn.execute("UPDATE alerts SET created_at = now() - interval '1 hour'")
        assert db.alert_recently_seen(conn, "k1", 300) is False

    def test_dedup_is_per_key(self, conn):
        db.insert_alert(conn, "Test", 5, {}, {}, "k1")
        assert db.alert_recently_seen(conn, "k2", 300) is False

    def test_list_respects_the_limit(self, conn):
        for i in range(5):
            db.insert_alert(conn, f"A{i}", 5, {}, {}, f"k{i}")
        assert len(db.list_alerts(conn, limit=3)) == 3


class TestCounts:
    def test_counts_events_pending_and_alerts(self, conn):
        add(conn, seconds=0)
        add(conn, seconds=1)
        db.claim_events(conn, 1)
        db.insert_alert(conn, "Test", 5, {}, {}, "k")
        got = db.counts(conn)
        assert (got["events"], got["pending"], got["alerts"]) == (2, 1, 1)
