"""The collector endpoints, against the real app and a real database."""


class TestIngest:
    def test_accepts_an_event_and_returns_its_id(self, client):
        res = client.post("/ingest", json={
            "timestamp": "2025-11-01T12:00:00Z",
            "source": "firewall",
            "event_type": "connection_blocked",
            "payload": {"ip": "1.2.3.4"},
        })
        assert res.status_code == 201
        assert res.json()["id"] > 0

    def test_timestamp_is_optional(self, client):
        res = client.post("/ingest", json={"source": "s", "event_type": "e", "payload": {}})
        assert res.status_code == 201

    def test_payload_is_optional(self, client):
        res = client.post("/ingest", json={"source": "s", "event_type": "e"})
        assert res.status_code == 201

    def test_rejects_an_event_with_no_source(self, client):
        assert client.post("/ingest", json={"event_type": "e"}).status_code == 422

    def test_rejects_an_empty_source(self, client):
        res = client.post("/ingest", json={"source": "", "event_type": "e"})
        assert res.status_code == 422

    def test_a_stored_event_shows_up_in_the_counts(self, client):
        client.post("/ingest", json={"source": "s", "event_type": "e"})
        assert client.get("/api/stats").json()["events"] == 1


class TestAlerts:
    def test_empty_to_start_with(self, client):
        assert client.get("/api/alerts").json() == []

    def test_rejects_a_silly_limit(self, client):
        assert client.get("/api/alerts?limit=0").status_code == 422
        assert client.get("/api/alerts?limit=99999").status_code == 422


class TestHealth:
    def test_reports_the_database_not_just_the_process(self, client):
        body = client.get("/health").json()
        assert body == {"status": "ok", "database": "ok"}

    def test_root_lists_the_endpoints(self, client):
        assert "/ingest" in client.get("/").json()["endpoints"]
