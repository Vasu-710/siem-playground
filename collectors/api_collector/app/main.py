"""The collector API.

Takes events in, hands alerts out. It does no detection of its own, it only
writes to the database the pipeline reads from.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from siemlib import db
from siemlib.normalizer import parse_timestamp

# Wildcard origins with credentials is a combination browsers reject outright,
# so the allowed origins are listed explicitly and can be set per deployment.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]


class Event(BaseModel):
    timestamp: str | None = None
    source: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = db.make_pool()
    with app.state.pool.connection() as conn:
        db.init_schema(conn)
    yield
    app.state.pool.close()


app = FastAPI(title="SIEM Playground Collector", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# These are sync handlers on purpose. The connection pool is a threaded pool,
# so FastAPI runs them in its worker threads rather than blocking the loop.
@app.post("/ingest", status_code=201)
def ingest(event: Event):
    with app.state.pool.connection() as conn:
        event_id = db.insert_event(
            conn,
            parse_timestamp(event.timestamp),
            event.source,
            event.event_type,
            event.payload,
        )
    return {"status": "queued", "id": event_id}


@app.get("/api/alerts")
def get_alerts(limit: int = Query(default=100, ge=1, le=1000)):
    with app.state.pool.connection() as conn:
        return db.list_alerts(conn, limit)


@app.get("/api/stats")
def get_stats():
    with app.state.pool.connection() as conn:
        return db.counts(conn)


@app.get("/health")
def health():
    """Reports the database too. A collector that cannot store an event is
    not healthy, however alive the process is."""
    try:
        with app.state.pool.connection() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}")
    return {"status": "ok", "database": "ok"}


@app.get("/")
def root():
    return {
        "service": "SIEM Playground Collector",
        "endpoints": ["/ingest", "/api/alerts", "/api/stats", "/health"],
    }
