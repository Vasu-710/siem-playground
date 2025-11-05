THREAT_DB = {
    "malicious_domain.com": {"score": 95, "source": "local-threat-db", "tags":["phishing"]},
    "1.2.3.4": {"score": 70, "source": "intel-sim", "tags":["botnet"]}
}

def enrich(evidence):
    # naive enrichment: check payload for domain/ip
    out = {}
    domain = evidence.get('payload', {}).get('domain')
    ip = evidence.get('payload', {}).get('ip')
    if domain and domain in THREAT_DB:
        out['domain_info'] = THREAT_DB[domain]
    if ip and ip in THREAT_DB:
        out['ip_info'] = THREAT_DB[ip]
    return out
