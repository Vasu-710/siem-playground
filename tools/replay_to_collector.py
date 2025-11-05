import requests, json, time
with open('datasets/demo_campaign_replay.json') as f:
    items = json.load(f)
for it in items:
    requests.post("http://localhost:8000/ingest", json=it)
    time.sleep(0.1)
print("replay done")
