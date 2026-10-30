"""Attach what we know about the indicators in an event.

The threat data is a dict in this file on purpose. Swapping it for a real feed
means replacing lookup() and nothing else.
"""

THREAT_DB = {
    "malicious_domain.com": {"score": 95, "source": "local-threat-db", "tags": ["phishing"]},
    "1.2.3.4": {"score": 70, "source": "intel-sim", "tags": ["botnet"]},
}


def lookup(indicator):
    """Return what is known about one indicator, or None."""
    if not indicator:
        return None
    return THREAT_DB.get(indicator)


def enrich(event):
    """Look up every indicator on an event and return what matched.

    An empty dict means nothing matched, which is different from not having
    looked.
    """
    payload = event.get("payload") or {}
    out = {}
    for field, key in (("domain", "domain_info"), ("ip", "ip_info")):
        value = event.get(field) or payload.get(field)
        hit = lookup(value)
        if hit:
            out[key] = dict(hit, indicator=value)
    return out
