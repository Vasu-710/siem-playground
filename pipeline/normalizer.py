import json
from datetime import datetime

def normalize(raw_event):
    # raw_event: dict parsed from the JSONL queue
    event = {}
    event['ts'] = raw_event.get('timestamp') or datetime.utcnow().isoformat()
    event['source'] = raw_event.get('source', 'unknown')
    event['type'] = raw_event.get('event_type', 'unknown')
    event['payload'] = raw_event.get('payload', {})
    # canonical fields for SIEM
    event['host'] = event['payload'].get('host')
    event['user'] = event['payload'].get('user')
    event['ip'] = event['payload'].get('ip')
    return event
