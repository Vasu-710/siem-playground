# SIEM Playground - Architecture Documentation

## Overview

SIEM Playground is a microservices-based security monitoring system that demonstrates core SIEM capabilities: event ingestion, normalization, correlation, enrichment, and visualization.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        SIEM Playground                        │
└──────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  Event Sources  │  (External systems, replay scripts, APIs)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Collector Layer                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI Collector (Port 8000)                      │   │
│  │  - REST endpoint: POST /ingest                      │   │
│  │  - Health check: GET /health                        │   │
│  │  - Alerts API: GET /api/alerts                      │   │
│  │  - CORS enabled for browser access                  │   │
│  └───────────────────┬─────────────────────────────────┘   │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │  Queue Storage │  (/tmp/siem_events.jsonl)
                └────────┬───────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Layer                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Pipeline Engine (correlator.py)                    │   │
│  │  ┌───────────────────────────────────────────────┐ │   │
│  │  │  1. Read events from queue                    │ │   │
│  │  │  2. Normalize (normalizer.py)                 │ │   │
│  │  │     - Parse timestamps                        │ │   │
│  │  │     - Extract canonical fields               │ │   │
│  │  │     - Standardize schema                     │ │   │
│  │  │  3. Apply Correlation Rules                   │ │   │
│  │  │     - Per-event rules                        │ │   │
│  │  │     - Windowed rules (multi-event)           │ │   │
│  │  │  4. Enrich (enricher.py)                      │ │   │
│  │  │     - Threat intelligence lookup             │ │   │
│  │  │     - IOC scoring                            │ │   │
│  │  │  5. Generate alerts                           │ │   │
│  │  └───────────────────────────────────────────────┘ │   │
│  └─────────────────────┬───────────────────────────────┘   │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │ Alerts Storage │  (/tmp/siem_alerts.jsonl)
                └────────┬───────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  React Dashboard (Port 3000)                        │   │
│  │  - Polls /api/alerts every 3 seconds               │   │
│  │  - Displays alerts with enrichment data            │   │
│  │  - Real-time updates                               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Storage Layer                            │
│  ┌─────────────────┐                                        │
│  │  PostgreSQL DB  │  (Port 5432)                           │
│  │  - Future: persistent event/alert storage                │
│  │  - Currently: supporting infrastructure                  │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Collector Service (FastAPI)

**Purpose:** Entry point for all security events

**Technology:** Python 3.11, FastAPI, Uvicorn

**Endpoints:**
- `POST /ingest` - Accept security events
- `GET /api/alerts` - Retrieve generated alerts
- `GET /health` - Health check endpoint
- `GET /` - API information

**Event Schema:**
```json
{
  "timestamp": "ISO8601 timestamp",
  "source": "string (e.g., 'firewall', 'ids', 'endpoint')",
  "event_type": "string (e.g., 'login_failed', 'connection_blocked')",
  "payload": {
    "arbitrary": "key-value pairs specific to event type"
  }
}
```

**Data Flow:**
1. Receives event via HTTP POST
2. Validates against Pydantic schema
3. Serializes to JSON
4. Appends to `/tmp/siem_events.jsonl` queue

**CORS:** Enabled for all origins to allow browser-based testing

---

### 2. Pipeline Engine

**Purpose:** Core processing logic for event correlation and enrichment

**Technology:** Python 3.11

**Components:**

#### 2.1 Normalizer (`normalizer.py`)

**Function:** Convert diverse log formats into a canonical schema

**Normalization Process:**
```python
{
  "ts": "2025-11-09T12:00:00Z",      # Standardized timestamp
  "source": "firewall",               # Event source
  "type": "connection_blocked",       # Event type
  "payload": {...},                   # Original payload
  "host": "web-server-01",           # Extracted canonical fields
  "user": "alice",
  "ip": "192.168.1.100"
}
```

**Benefits:**
- Enables cross-source correlation
- Simplifies rule writing
- Improves query performance

#### 2.2 Correlator (`correlator.py`)

**Function:** Apply detection rules to identify threats

**Rule Types:**

1. **Per-Event Rules**
   - Evaluate each event individually
   - Example: Credential submission detection
   ```python
   def rule_credential_submission(evt):
       if evt['type'] == 'credential_submitted':
           return {"name": "Credential Submission", "severity": 7}
   ```

2. **Windowed Rules**
   - Analyze patterns across multiple events
   - Example: Mass link clicks in phishing campaign
   ```python
   def rule_mass_clicks(recent_events):
       counts = {}
       for e in recent_events:
           if e['type'] == 'link_clicked':
               counts[e['campaign_id']] += 1
       if max(counts.values()) >= 5:
           return {"name": "Mass Clicks", "severity": 5}
   ```

**Alert Structure:**
```json
{
  "name": "Credential Submission",
  "severity": 7,
  "evidence": {...},
  "enriched": {...}
}
```

**Processing Loop:**
1. Read events from queue every 1 second
2. Normalize each event
3. Apply per-event rules
4. Apply windowed rules on recent event buffer (50 events)
5. Enrich alerts with threat intelligence
6. Write alerts to `/tmp/siem_alerts.jsonl`
7. Clear processed events from queue

#### 2.3 Enricher (`enricher.py`)

**Function:** Add threat intelligence context to alerts

**Threat Database:**
```python
THREAT_DB = {
    "malicious_domain.com": {
        "score": 95,
        "source": "local-threat-db",
        "tags": ["phishing"]
    },
    "1.2.3.4": {
        "score": 70,
        "source": "intel-sim",
        "tags": ["botnet"]
    }
}
```

**Enrichment Logic:**
- Extract IOCs (domains, IPs) from event payload
- Lookup in threat database
- Add reputation scores and tags
- Attach to alert as `enriched` field

**Future Enhancements:**
- Integration with VirusTotal API
- AbuseIPDB lookups
- MITRE ATT&CK mapping
- Geo-IP enrichment

---

### 3. React Dashboard

**Purpose:** Real-time visualization of security alerts

**Technology:** React 18, Node.js 20

**Features:**
- Auto-refresh every 3 seconds
- Error handling with user feedback
- Loading states
- Pretty-printed JSON enrichment data

**Data Flow:**
1. `useEffect` hook triggers on mount
2. Fetch alerts from `GET /api/alerts`
3. Update state with `setAlerts()`
4. Re-render component with new data
5. Repeat every 3 seconds via `setInterval`

**UI States:**
- **Loading:** "Loading alerts..."
- **Error:** Red error message with details
- **No Alerts:** "No alerts yet. Replay demo telemetry..."
- **Alerts Present:** Card-based display with severity and enrichment

---

### 4. PostgreSQL Database

**Purpose:** Persistent storage layer (future enhancement)

**Current State:**
- Running as supporting infrastructure
- Not actively used for storage
- Events/alerts stored in temporary JSON files

**Future Use Cases:**
- Persistent event history
- Alert archival
- User authentication
- Dashboard configurations
- Historical analytics

---

## Data Flow

### End-to-End Event Processing

```
1. EVENT INGESTION
   External Source → POST /ingest → Collector validates → Write to queue

2. NORMALIZATION
   Queue → Pipeline reads → Normalizer standardizes → Canonical event

3. CORRELATION
   Normalized event → Rule engine → Pattern matching → Alert generated?

4. ENRICHMENT
   Alert → Enricher → Threat DB lookup → IOC scoring → Enriched alert

5. STORAGE
   Enriched alert → JSON file → /tmp/siem_alerts.jsonl

6. VISUALIZATION
   React UI → GET /api/alerts → Collector reads file → Display in dashboard
```

---

## File System Layout

### Temporary Storage

**Event Queue:** `/tmp/siem_events.jsonl`
- Format: JSONL (one JSON object per line)
- Written by: Collector
- Read by: Pipeline
- Cleared: After processing (demo mode)

**Alerts Storage:** `/tmp/siem_alerts.jsonl`
- Format: JSONL
- Written by: Pipeline
- Read by: Collector (for API), UI (via API)
- Persistence: Append-only, never cleared

### Volume Mounts

```yaml
collector:
  volumes:
    - /tmp:/tmp          # Share temp files

pipeline:
  volumes:
    - ./pipeline:/app    # Live code reload
    - /tmp:/tmp          # Share temp files
```

---

## Scalability Considerations

### Current Limitations

1. **Single-threaded pipeline** - Processes events sequentially
2. **In-memory state** - No persistence across restarts
3. **File-based queue** - Not suitable for high throughput
4. **No partitioning** - All events in single queue

### Production Recommendations

1. **Replace file queue with message broker:**
   - Kafka, RabbitMQ, or Redis Streams
   - Enables horizontal scaling

2. **Implement persistent storage:**
   - PostgreSQL for structured alerts
   - Elasticsearch for full-text search
   - S3/Object storage for raw logs

3. **Add caching layer:**
   - Redis for threat intel lookups
   - Reduce external API calls

4. **Containerize with orchestration:**
   - Kubernetes for auto-scaling
   - Health checks and self-healing

5. **Implement batching:**
   - Process events in batches
   - Improve throughput

---

## Security Considerations

### Current Implementation

- **No authentication** - Open API endpoints
- **No encryption** - Plain HTTP
- **CORS wide open** - `allow_origins=["*"]`
- **No input validation** - Beyond Pydantic schema
- **No rate limiting** - Vulnerable to DoS

### Production Requirements

1. **Authentication & Authorization:**
   - API keys or OAuth2
   - Role-based access control (RBAC)

2. **Encryption:**
   - TLS/SSL for all communications
   - Encrypted storage for sensitive data

3. **Input Validation:**
   - Strict schema enforcement
   - Sanitization of user inputs
   - Size limits on payloads

4. **Rate Limiting:**
   - Per-IP throttling
   - API quotas

5. **Audit Logging:**
   - Track all API access
   - Log correlation rule changes

---

## Monitoring & Observability

### Current State

- Docker logs via `docker-compose logs`
- Manual inspection of temp files
- React UI for alert viewing

### Recommended Additions

1. **Metrics:**
   - Prometheus for service metrics
   - Grafana for dashboards
   - Track: events/sec, alert rate, latency

2. **Distributed Tracing:**
   - Jaeger or Zipkin
   - Trace events end-to-end

3. **Structured Logging:**
   - JSON formatted logs
   - Centralized log aggregation (ELK)

4. **Health Checks:**
   - Liveness probes
   - Readiness probes
   - Dependency checks

---

## Extension Points

### Adding New Event Sources

1. Create collector plugin in `collectors/`
2. Implement normalization logic
3. Configure pipeline to process new event types

### Adding Correlation Rules

1. Define rule function in `correlator.py`
2. Return alert dict or `None`
3. Rules automatically applied to all events

### Adding Threat Intelligence Sources

1. Update `THREAT_DB` in `enricher.py`
2. Or integrate external APIs (VirusTotal, etc.)
3. Add error handling for API failures

### Custom Dashboards

1. Modify `ui/src/App.js`
2. Add new components for visualizations
3. Use charting libraries (recharts, d3.js)

---

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Collector API | FastAPI | 0.112.0 | Event ingestion |
| API Server | Uvicorn | 0.23.1 | ASGI server |
| Data Validation | Pydantic | 2.5.1 | Schema validation |
| Pipeline | Python | 3.11 | Event processing |
| Database | PostgreSQL | 15 | Persistent storage |
| Frontend | React | 18.2.0 | Dashboard UI |
| Node Runtime | Node.js | 20 | JavaScript runtime |
| Container | Docker | - | Containerization |
| Orchestration | Docker Compose | - | Multi-container apps |

---

## Future Architecture Vision

```
┌──────────────────────────────────────────────────────────┐
│                    Load Balancer                          │
└────────────────────────┬─────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Collector│    │Collector│    │Collector│  (Scaled)
    └────┬────┘    └────┬────┘    └────┬────┘
         └──────────────┼──────────────┘
                        ▼
                 ┌──────────────┐
                 │     Kafka     │  (Message Broker)
                 └──────┬───────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │Pipeline │   │Pipeline │   │Pipeline │  (Parallel)
    └────┬────┘   └────┬────┘   └────┬────┘
         └─────────────┼─────────────┘
                       ▼
          ┌────────────────────────┐
          │   Elasticsearch        │  (Fast search)
          │   PostgreSQL           │  (Structured data)
          │   Redis                │  (Cache)
          └────────────┬───────────┘
                       ▼
              ┌─────────────────┐
              │   React UI      │
              │   + Kibana      │
              └─────────────────┘
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Author:** Vasu Saini