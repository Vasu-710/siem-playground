from datetime import datetime, timedelta, timezone

from siemlib import rules
from siemlib.normalizer import normalize

BASE = datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)


def click(campaign, seconds=0, ip=None):
    return normalize({
        "timestamp": (BASE + timedelta(seconds=seconds)).isoformat(),
        "source": "redteam",
        "event_type": "link_clicked",
        "payload": {"campaign_id": campaign, "ip": ip},
    })


class TestCredentialSubmission:
    def test_fires_on_a_credential_event(self):
        event = normalize({
            "event_type": "credential_submitted",
            "payload": {"campaign_id": "camp1", "username": "alice"},
        })
        alert = rules.credential_submission(event)
        assert alert["name"] == "Credential Submission"
        assert alert["severity"] == 7

    def test_ignores_everything_else(self):
        assert rules.credential_submission(click("camp1")) is None

    def test_dedup_key_separates_users_in_one_campaign(self):
        def key(user):
            event = normalize({
                "event_type": "credential_submitted",
                "payload": {"campaign_id": "camp1", "username": user},
            })
            return rules.credential_submission(event)["dedup_key"]

        assert key("alice") != key("bob")

    def test_evidence_is_json_safe(self):
        event = normalize({"event_type": "credential_submitted", "payload": {}})
        assert isinstance(rules.credential_submission(event)["evidence"]["event"]["ts"], str)


class TestMassClicks:
    def test_fires_at_the_threshold(self):
        events = [click("camp1", seconds=i) for i in range(5)]
        alerts = rules.mass_clicks(events)
        assert len(alerts) == 1
        assert alerts[0]["evidence"]["clicks"] == 5

    def test_stays_quiet_below_the_threshold(self):
        assert rules.mass_clicks([click("camp1", seconds=i) for i in range(4)]) == []

    def test_counts_each_campaign_separately(self):
        events = [click("camp1", seconds=i) for i in range(4)]
        events += [click("camp2", seconds=i) for i in range(4)]
        assert rules.mass_clicks(events) == []

    def test_reports_every_campaign_over_the_threshold(self):
        """The old version returned on the first match and dropped the rest."""
        events = [click("camp1", seconds=i) for i in range(5)]
        events += [click("camp2", seconds=i) for i in range(6)]
        alerts = rules.mass_clicks(events)
        assert [a["evidence"]["campaign_id"] for a in alerts] == ["camp1", "camp2"]

    def test_ignores_events_that_are_not_clicks(self):
        noise = [normalize({"event_type": "email_sent", "payload": {"campaign_id": "camp1"}})
                 for _ in range(10)]
        assert rules.mass_clicks(noise) == []

    def test_skips_clicks_with_no_campaign(self):
        assert rules.mass_clicks([click(None) for _ in range(10)]) == []

    def test_enriches_from_the_latest_click(self):
        events = [click("camp1", seconds=i) for i in range(4)]
        events.append(click("camp1", seconds=99, ip="1.2.3.4"))
        alert = rules.mass_clicks(events)[0]
        assert alert["enrich_from"]["ip"] == "1.2.3.4"

    def test_threshold_is_adjustable(self):
        assert len(rules.mass_clicks([click("camp1")], threshold=1)) == 1

    def test_dedup_key_is_stable_for_one_campaign(self):
        a = rules.mass_clicks([click("camp1", seconds=i) for i in range(5)])[0]
        b = rules.mass_clicks([click("camp1", seconds=i) for i in range(6)])[0]
        assert a["dedup_key"] == b["dedup_key"]


class TestRuleRegistry:
    def test_every_registered_rule_is_callable(self):
        for rule in rules.PER_EVENT_RULES + rules.WINDOWED_RULES:
            assert callable(rule)

    def test_alerts_carry_every_field_the_pipeline_needs(self):
        event = normalize({"event_type": "credential_submitted", "payload": {}})
        alert = rules.credential_submission(event)
        assert set(alert) == {"name", "severity", "evidence", "dedup_key", "enrich_from"}
