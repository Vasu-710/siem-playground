"""Shared fixtures.

The database tests need a real Postgres because the thing being tested is the
SQL, not a mock of it. They skip when none is reachable so the pure unit tests
still run anywhere.
"""

import os

import pytest

DB_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def conn():
    if not DB_URL:
        pytest.skip("set TEST_DATABASE_URL to run the database tests")

    os.environ["DATABASE_URL"] = DB_URL
    from siemlib import db

    connection = db.connect()
    db.init_schema(connection)
    connection.execute("TRUNCATE events, alerts RESTART IDENTITY")
    yield connection
    connection.close()


@pytest.fixture
def client(conn):
    """A test client against the real app, backed by the real database."""
    from fastapi.testclient import TestClient

    from collectors.api_collector.app.main import app

    with TestClient(app) as test_client:
        yield test_client
