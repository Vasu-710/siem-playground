"""End to end: events in the database, alerts out, through the real rules."""

from datetime import datetime, timedelta, timezone

from siemlib import db

BASE = datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)


def add(conn, event_type, payload=None, seconds=0):
    db.insert_event(
        conn,
        datetime.now(timezone.utc) - timedelta(seconds=seconds),
        "redteam",
        event_type,
        payload or {},
    )


class TestProcessOnce:
    def test_no_events_means_no_alerts(self, conn):
        from pipeline import correlator
        assert correlator.process_once(conn) == 0

    def test_a_credential_event_produces_an_enriched_alert(self, conn):
        from pipeline import correlator
        add(conn, "credential_submitted",
            {"campaign_id": "camp1", "username": "alice", "ip": "1.2.3.4"})

        assert correlator.process_once(conn) == 1
        alert = db.list_alerts(conn)[0]
        assert alert["name"] == "Credential Submission"
        assert alert["enrichment"]["ip_info"]["score"] == 70

    def test_the_same_condition_does_not_alert_twice(self, conn):
        from pipeline import correlator
        add(conn, "credential_submitted", {"campaign_id": "camp1", "username": "alice"})
        correlator.process_once(conn)
        add(conn, "credential_submitted", {"campaign_id": "camp1", "username": "alice"})
        assert correlator.process_once(conn) == 0
        assert len(db.list_alerts(conn)) == 1

    def test_a_different_user_still_alerts(self, conn):
        from pipeline import correlator
        add(conn, "credential_submitted", {"campaign_id": "camp1", "username": "alice"})
        correlator.process_once(conn)
        add(conn, "credential_submitted", {"campaign_id": "camp1", "username": "bob"})
        assert correlator.process_once(conn) == 1

    def test_mass_clicks_fires_once_the_window_holds_enough(self, conn):
        from pipeline import correlator
        for i in range(5):
            add(conn, "link_clicked", {"campaign_id": "camp1", "ip": "1.2.3.4"}, seconds=i)

        assert correlator.process_once(conn) == 1
        alert = db.list_alerts(conn)[0]
        assert alert["name"] == "Mass Clicks"
        assert alert["evidence"]["clicks"] == 5
        # The old version hardcoded this to empty.
        assert alert["enrichment"]["ip_info"]["indicator"] == "1.2.3.4"

    def test_every_event_is_marked_processed(self, conn):
        from pipeline import correlator
        for i in range(3):
            add(conn, "link_clicked", {"campaign_id": "camp1"}, seconds=i)
        correlator.process_once(conn)
        assert db.counts(conn)["pending"] == 0

    def test_the_demo_dataset_produces_the_expected_alert(self, conn):
        """Whatever else changes, the shipped demo must still do something."""
        import json
        import pathlib
        from siemlib.normalizer import parse_timestamp

        data = json.loads(pathlib.Path("datasets/demo_campaign_replay.json").read_text())
        for item in data:
            db.insert_event(
                conn, parse_timestamp(item["timestamp"]),
                item["source"], item["event_type"], item["payload"],
            )

        from pipeline import correlator
        assert correlator.process_once(conn) == 1
        assert db.list_alerts(conn)[0]["name"] == "Credential Submission"
