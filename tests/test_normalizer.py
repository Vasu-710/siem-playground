from datetime import datetime, timezone

from siemlib.normalizer import as_json, normalize, parse_timestamp


class TestParseTimestamp:
    def test_parses_iso_with_trailing_z(self):
        got = parse_timestamp("2025-11-01T12:00:00Z")
        assert got == datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)

    def test_parses_iso_with_offset(self):
        got = parse_timestamp("2025-11-01T13:00:00+01:00")
        assert got == datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)

    def test_assumes_utc_when_no_zone_is_given(self):
        assert parse_timestamp("2025-11-01T12:00:00").tzinfo == timezone.utc

    def test_passes_a_datetime_straight_through(self):
        when = datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)
        assert parse_timestamp(when) == when

    def test_falls_back_to_now_rather_than_raising(self):
        # A sender with a broken clock format should not stop ingestion.
        for bad in ("not a date", "", None, 12345.6):
            assert parse_timestamp(bad).tzinfo == timezone.utc

    def test_result_is_always_timezone_aware(self):
        assert parse_timestamp(datetime(2025, 1, 1)).tzinfo == timezone.utc


class TestNormalize:
    def test_maps_the_canonical_fields(self):
        event = normalize({
            "timestamp": "2025-11-01T12:00:00Z",
            "source": "redteam",
            "event_type": "link_clicked",
            "payload": {"ip": "1.2.3.4", "host": "box1", "domain": "evil.test"},
        })
        assert event["source"] == "redteam"
        assert event["type"] == "link_clicked"
        assert event["ip"] == "1.2.3.4"
        assert event["host"] == "box1"
        assert event["domain"] == "evil.test"

    def test_reads_username_as_well_as_user(self):
        # The demo dataset sends username, the rules read user.
        assert normalize({"payload": {"username": "alice"}})["user"] == "alice"
        assert normalize({"payload": {"user": "bob"}})["user"] == "bob"

    def test_accepts_database_rows_which_use_ts_and_type(self):
        row = {
            "ts": datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc),
            "source": "db",
            "event_type": "credential_submitted",
            "payload": {},
            "id": 7,
        }
        event = normalize(row)
        assert event["id"] == 7
        assert event["type"] == "credential_submitted"

    def test_missing_fields_become_unknown_not_crashes(self):
        event = normalize({})
        assert event["source"] == "unknown"
        assert event["type"] == "unknown"
        assert event["payload"] == {}

    def test_a_non_dict_payload_does_not_break_the_rules(self):
        assert normalize({"payload": "just a string"})["payload"] == {"value": "just a string"}
        assert normalize({"payload": None})["payload"] == {}


class TestAsJson:
    def test_converts_the_timestamp_so_it_can_be_stored(self):
        event = normalize({"timestamp": "2025-11-01T12:00:00Z", "payload": {}})
        assert as_json(event)["ts"] == "2025-11-01T12:00:00+00:00"

    def test_does_not_mutate_the_original(self):
        event = normalize({"timestamp": "2025-11-01T12:00:00Z", "payload": {}})
        as_json(event)
        assert isinstance(event["ts"], datetime)
