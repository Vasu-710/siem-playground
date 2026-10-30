from siemlib.enricher import enrich, lookup
from siemlib.normalizer import normalize


class TestLookup:
    def test_known_indicator_returns_its_record(self):
        assert lookup("1.2.3.4")["score"] == 70

    def test_unknown_indicator_returns_none(self):
        assert lookup("8.8.8.8") is None

    def test_empty_indicator_returns_none(self):
        assert lookup(None) is None
        assert lookup("") is None


class TestEnrich:
    def test_matches_both_ip_and_domain(self):
        event = normalize({"payload": {"ip": "1.2.3.4", "domain": "malicious_domain.com"}})
        out = enrich(event)
        assert out["ip_info"]["indicator"] == "1.2.3.4"
        assert out["domain_info"]["tags"] == ["phishing"]

    def test_no_match_returns_an_empty_dict(self):
        # Empty means nothing matched. It does not mean nobody looked.
        assert enrich(normalize({"payload": {"ip": "8.8.8.8"}})) == {}

    def test_event_with_no_indicators_is_fine(self):
        assert enrich(normalize({})) == {}

    def test_does_not_mutate_the_threat_record(self):
        event = normalize({"payload": {"ip": "1.2.3.4"}})
        enrich(event)
        assert "indicator" not in lookup("1.2.3.4")
