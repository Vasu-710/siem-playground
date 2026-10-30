"""Turn whatever arrives into one canonical event shape.

Every rule downstream assumes these keys exist, so this is the only place that
has to care what a source happened to call a field.
"""

from datetime import datetime, timezone


def parse_timestamp(value):
    """Return a timezone-aware UTC datetime, falling back to now().

    Accepts a datetime, an ISO 8601 string with or without a trailing Z, or
    nothing at all. A sender with a broken clock format should not take the
    pipeline down with it.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if not value:
        return datetime.now(timezone.utc)

    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize(raw_event):
    """Map a raw event onto the canonical fields the rules read."""
    payload = raw_event.get("payload")
    if not isinstance(payload, dict):
        payload = {} if payload is None else {"value": payload}

    return {
        "id": raw_event.get("id"),
        "ts": parse_timestamp(raw_event.get("timestamp") or raw_event.get("ts")),
        "source": raw_event.get("source") or "unknown",
        "type": raw_event.get("event_type") or raw_event.get("type") or "unknown",
        "payload": payload,
        "host": payload.get("host"),
        "user": payload.get("user") or payload.get("username"),
        "ip": payload.get("ip"),
        "domain": payload.get("domain"),
    }


def as_json(event):
    """A copy of the event safe to hand to psycopg as JSONB."""
    out = dict(event)
    ts = out.get("ts")
    if isinstance(ts, datetime):
        out["ts"] = ts.isoformat()
    return out
