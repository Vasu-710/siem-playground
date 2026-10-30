# SIEM Playground

![Python Tests](https://github.com/Vasu-710/siem-playground/actions/workflows/python-tests.yml/badge.svg)
![UI Lint & Test](https://github.com/Vasu-710/siem-playground/actions/workflows/ui-workflow.yml/badge.svg)
[![codecov](https://codecov.io/gh/Vasu-710/siem-playground/branch/main/graph/badge.svg)](https://codecov.io/gh/Vasu-710/siem-playground)

A small SIEM pipeline you can run on a laptop. Events go in over HTTP, get
normalised and checked against detection rules, and alerts come out on a
dashboard. Built to learn how the pieces of a SIEM fit together, not to
replace one.

## How it works

```
  POST /ingest                  claim unprocessed rows
       │                                  │
       ▼                                  ▼
┌──────────────┐   events    ┌─────────────────────────┐   alerts
│  Collector   │ ──────────> │        Pipeline         │ ─────────┐
│  (FastAPI)   │             │ normalise → rules →     │          │
└──────────────┘             │ enrich → store          │          │
       ▲                     └─────────────────────────┘          │
       │                                  │                       │
       │                                  ▼                       ▼
       │                        ┌────────────────────────────────────┐
       │                        │             PostgreSQL             │
       │                        │        events  ·  alerts           │
       │                        └────────────────────────────────────┘
       │                                          │
  GET /api/alerts  <──────────────────────────────┘
       │
       ▼
┌──────────────┐
│  React UI    │  polls every 3s
└──────────────┘
```

The collector never decides anything. It writes events and reads alerts. All
detection happens in the pipeline, which claims rows from the database rather
than reading a file, so an event is handed to exactly one pass and is never
dropped.

## Quick start

Needs Docker and Docker Compose.

```bash
git clone https://github.com/Vasu-710/siem-playground.git
cd siem-playground
docker compose up --build
```

Then send the demo campaign through it:

```bash
pip install requests
python tools/replay_to_collector.py
```

Open http://localhost:3000. The replay waits for the collector to be healthy
before sending, and the pipeline polls once a second, so alerts show up within
a few seconds.

Send your own event:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"firewall","event_type":"connection_blocked",
       "payload":{"ip":"1.2.3.4","port":445}}'
```

| Endpoint | What it does |
|---|---|
| `POST /ingest` | Store one event. `timestamp` and `payload` are optional |
| `GET /api/alerts?limit=100` | Most recent alerts first |
| `GET /api/stats` | Event, pending and alert counts |
| `GET /health` | Checks the database, not just the process |

## The detection rules

Both live in `siemlib/rules.py`.

**Credential Submission** (severity 7) fires on a single `credential_submitted`
event. Deduplicated per campaign and user.

**Mass Clicks** (severity 5) fires when one campaign collects five or more
`link_clicked` events inside the window. Deduplicated per campaign.

Rules are plain functions over normalised events. They take no database
connection and read no clock, which is why they can be tested against a fixed
list. The caller decides what "recent" means and passes it in.

To add one, write the function and add it to `PER_EVENT_RULES` or
`WINDOWED_RULES`:

```python
def brute_force(events, threshold=5):
    failures = [e for e in events if e["type"] == "auth_failed"]
    if len(failures) < threshold:
        return []
    return [{
        "name": "Brute Force",
        "severity": 8,
        "evidence": {"attempts": len(failures)},
        "dedup_key": f"brute_force:{failures[-1]['user']}",
        "enrich_from": failures[-1],
    }]
```

## Threat enrichment

`siemlib/enricher.py` holds a dict of indicators. Every alert gets its IP and
domain looked up, and whatever matches is stored alongside it. An empty
`enrichment` means nothing matched, which is not the same as nobody having
looked. Swapping the dict for a real feed means replacing `lookup()` and
nothing else.

## Configuration

| Variable | Default | Used by |
|---|---|---|
| `DATABASE_URL` | `postgresql://siem:siem_pass@db:5432/siemdb` | both |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | collector |
| `BATCH_SIZE` | `100` | pipeline |
| `WINDOW_SECONDS` | `300` | pipeline |
| `DEDUP_SECONDS` | `300` | pipeline |
| `POLL_SECONDS` | `1` | pipeline |
| `LOG_LEVEL` | `INFO` | pipeline |

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

The unit tests run anywhere. The database tests need a real Postgres and skip
without one, because what they are testing is the SQL and a mock would only
test the mock:

```bash
docker compose up -d db
TEST_DATABASE_URL=postgresql://siem:siem_pass@localhost:5432/siemdb pytest tests/
```

UI:

```bash
cd ui
npm ci
npm run lint
npm test -- --watchAll=false
```

CI runs all of it on every push, including a Postgres service container.

## Layout

```
siemlib/            shared by both services
  normalizer.py     raw event  ->  canonical fields
  rules.py          detection rules, pure functions
  enricher.py       indicator lookup
  db.py             all the SQL
  schema.sql        tables and indexes
collectors/api_collector/app/main.py    the HTTP API
pipeline/correlator.py                  the loop
ui/src/                                 React dashboard
tests/                                  65 tests
tools/replay_to_collector.py            send a dataset in
datasets/                               demo phishing campaign
```

## What it does not do

- **No authentication.** Anyone who can reach the collector can write events
  and read every alert. Fine on a laptop, not fine anywhere else.
- **Two rules.** Real SIEMs have hundreds.
- **The threat data is a dict in a file.** No live feeds.
- **One pipeline process.** `FOR UPDATE SKIP LOCKED` means a second one would
  be safe, but nothing has been tested that way.
- **Nothing is ever deleted.** Events and alerts accumulate until you drop the
  volume.
- **No alert routing.** Alerts land in the database and on the dashboard. They
  do not go anywhere else.

## History

This started as a learning project in November 2025 and was rewritten in
October 2026. A few things were wrong with the first version and they are worth
writing down.

**The UI workflow checked nothing.** The steps were
`npm run lint || echo "Lint warnings"` and `npm test || echo "Tests run"`.
There was no `lint` script and there were no test files, so both commands
failed every run, `|| echo` swallowed the failure, and the badge said passing.
Ten green runs that never linted or tested a single line.

**The pipeline silently lost events.** Events were appended to a JSONL file in
`/tmp`. Each pass read the whole file, processed it, then truncated it.
Anything the collector appended between the read and the truncate was gone with
no error and no trace. Events now live in Postgres and are claimed with
`UPDATE ... WHERE id IN (SELECT ... FOR UPDATE SKIP LOCKED)`, so a row is
handed to exactly one pass.

**Postgres was started but never used.** Compose ran it, the README listed it
under Quick Start and also called it a future enhancement, and no code imported
a database driver. It is now the actual storage.

**The mass clicks rule had no window** despite a comment saying it did, only
ever saw whatever arrived in the last second, returned on the first campaign it
found, and its alerts were hardcoded to have no enrichment.

**The coverage badge measured one file.** Coverage ran with no `--source`, so
it only counted modules the single test imported, and reported that as the
project's number.

**CORS allowed all origins with credentials enabled**, a combination browsers
reject outright.

The pattern in most of those is the same. Something reported success based on
having run rather than on what it produced. That is worth more to me than the
project is.
