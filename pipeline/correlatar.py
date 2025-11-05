import time, json, os
from normalizer import normalize
from enricher import enrich

QUEUE_FILE = "/tmp/siem_events.jsonl"
ALERTS_FILE = "/tmp/siem_alerts.jsonl"

# simple rules: list of functions that return alert dict or None
def rule_credential_submission(evt):
    if evt['type'] == 'credential_submitted':
        return {"name": "Credential Submission", "severity": 7, "evidence": evt}
    return None

def rule_mass_clicks(recent_events):
    # naive: if >5 link_clicked from same campaign within window -> suspicious
    counts = {}
    for e in recent_events:
        if e['type'] == 'link_clicked':
            camp = e['payload'].get('campaign_id')
            counts[camp] = counts.get(camp, 0) + 1
            if counts[camp] >= 5:
                return {"name": "Mass Clicks", "severity": 5, "evidence": {"campaign": camp}}
    return None

def read_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE) as f:
        lines = [json.loads(l) for l in f if l.strip()]
    return lines

def main_loop():
    processed = 0
    while True:
        raw = read_queue()
        if not raw:
            time.sleep(1)
            continue
        events = [normalize(r) for r in raw]
        # run per-event rules
        for e in events:
            a = rule_credential_submission(e)
            if a:
                a['enriched'] = enrich(a['evidence'])
                with open(ALERTS_FILE, "a") as f:
                    f.write(json.dumps(a) + "\n")
        # run windowed rule
        a2 = rule_mass_clicks(events[-50:])
        if a2:
            a2['enriched'] = {}
            with open(ALERTS_FILE, "a") as f:
                f.write(json.dumps(a2) + "\n")
        # simple rotation: clear queue after processing (for demo)
        open(QUEUE_FILE, "w").close()
        processed += 1
        time.sleep(1)

if __name__ == "__main__":
    main_loop()
