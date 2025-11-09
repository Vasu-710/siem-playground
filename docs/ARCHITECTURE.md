# SIEM Playground Architecture

**Goal:** Lightweight SIEM and Threat Enrichment Playground.

### Components
- **Collectors:** ingest logs/events from demo sources.
- **Pipeline:** normalizes + correlates + enriches data.
- **Storage:** temporary datastore (could be Postgres or JSON).
- **UI:** React dashboard showing live alerts.
- **Tools:** replay sample events and simulate detections.

### Flow
1. Collector ingests → sends to pipeline.
2. Normalizer parses, Enricher adds threat intel.
3. Correlater applies rules → generates alert.
4. Alerts appear in the UI (React frontend).
