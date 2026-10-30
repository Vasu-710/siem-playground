"""Replay a dataset into the collector.

Usage:
    python tools/replay_to_collector.py [dataset.json] [--url http://localhost:8000]
"""

import argparse
import json
import pathlib
import sys
import time

import requests

DEFAULT_DATASET = pathlib.Path(__file__).resolve().parent.parent / "datasets" / "demo_campaign_replay.json"


def wait_for_collector(url, attempts=30, delay=1.0):
    for _ in range(attempts):
        try:
            if requests.get(f"{url}/health", timeout=2).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(delay)
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", nargs="?", default=str(DEFAULT_DATASET))
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--delay", type=float, default=0.1)
    args = parser.parse_args()

    url = args.url.rstrip("/")
    if not wait_for_collector(url):
        sys.exit(f"Collector at {url} never became healthy. Is the stack up?")

    events = json.loads(pathlib.Path(args.dataset).read_text())

    sent = 0
    for event in events:
        response = requests.post(f"{url}/ingest", json=event, timeout=5)
        if response.status_code != 201:
            sys.exit(f"Collector rejected event {sent + 1}: {response.status_code} {response.text}")
        sent += 1
        time.sleep(args.delay)

    print(f"Sent {sent} event(s) to {url}")
    print("The pipeline polls once a second, so alerts should appear shortly.")


if __name__ == "__main__":
    main()
