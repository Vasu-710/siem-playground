"""Detection rules.

Every rule is a plain function over already-normalised events. No database, no
clock, no files. The caller decides what counts as "recent" and passes it in,
which is what makes these testable with a fixed list.

A rule returns a dict with:
    name        what the alert is called
    severity    1 to 10
    evidence    what gets stored as JSONB
    dedup_key   identity of the thing being alerted on, so the same condition
                does not raise an alert on every pass
    enrich_from the event whose indicators should be looked up
"""

from .normalizer import as_json

MASS_CLICK_THRESHOLD = 5


def credential_submission(event):
    """Someone submitted credentials. One event is enough to care."""
    if event["type"] != "credential_submitted":
        return None

    campaign = event["payload"].get("campaign_id", "unknown")
    user = event.get("user") or "unknown"
    return {
        "name": "Credential Submission",
        "severity": 7,
        "evidence": {"event": as_json(event)},
        "dedup_key": f"credential_submission:{campaign}:{user}",
        "enrich_from": event,
    }


def mass_clicks(events, threshold=MASS_CLICK_THRESHOLD):
    """One campaign collecting a lot of clicks in the caller's window.

    Returns a list, because two campaigns can both be over the threshold in the
    same window. The old version returned on the first match and silently
    dropped the rest.
    """
    by_campaign = {}
    for event in events:
        if event["type"] != "link_clicked":
            continue
        campaign = event["payload"].get("campaign_id")
        if campaign is None:
            continue
        by_campaign.setdefault(campaign, []).append(event)

    alerts = []
    for campaign in sorted(by_campaign):
        clicks = by_campaign[campaign]
        if len(clicks) < threshold:
            continue
        latest = max(clicks, key=lambda e: e["ts"])
        alerts.append({
            "name": "Mass Clicks",
            "severity": 5,
            "evidence": {
                "campaign_id": campaign,
                "clicks": len(clicks),
                "latest_event": as_json(latest),
            },
            "dedup_key": f"mass_clicks:{campaign}",
            "enrich_from": latest,
        })
    return alerts


PER_EVENT_RULES = (credential_submission,)
WINDOWED_RULES = (mass_clicks,)
