from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, requests, json

app = FastAPI(title="SIEM Playground Collector")

class Event(BaseModel):
    timestamp: str
    source: str
    event_type: str
    payload: dict

# naive in-memory queue (pipeline reads from this file or poll)
QUEUE_FILE = "/tmp/siem_events.jsonl"

@app.post("/ingest")
async def ingest(e: Event):
    line = e.json()
    with open(QUEUE_FILE, "a") as f:
        f.write(line + "\n")
    return {"status": "queued"}

@app.get("/health")
def health():
    return {"status": "ok"}
