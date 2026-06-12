"""Integration tests for the upload workflow, dedupe, and dashboard aggregation.

These require a PostgreSQL instance (the dedupe upserts use PG ``ON CONFLICT``).
Point ``TEST_DATABASE_URL`` at a disposable database; tests skip if unreachable.
Inside docker-compose the default URL works out of the box.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  (must precede the alias import below)
from app.database.base import Base
from app.database.session import get_db
from app.main import app as fastapi_app  # alias: `import app.models` rebinds `app`

from tests.conftest import build_xlsx

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://linkedin:linkedin@localhost:5432/linkedin_test"
)


@pytest.fixture(scope="module")
def client():
    try:
        engine = create_engine(TEST_DB_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        pytest.skip("PostgreSQL not available for integration tests")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = TestingSession()
        try:
            yield db
            db.commit()
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def _upload(client, data, name):
    return client.post("/api/uploads", files={"file": (name, data)})


def test_upload_workflow_and_dedupe(client, content_xlsx):
    r = _upload(client, content_xlsx, "content.xlsx")
    assert r.status_code == 201
    body = r.json()
    assert body["upload"]["upload_type"] == "content"
    assert body["report"]["posts"] == 2

    # Re-uploading identical content is a no-op (content hashing).
    r2 = _upload(client, content_xlsx, "content.xlsx")
    assert r2.json()["duplicate"] is True

    assert len(client.get("/api/uploads").json()) == 1


def test_dashboard_aggregation(client, followers_xlsx, visitors_xlsx):
    _upload(client, followers_xlsx, "followers.xlsx")
    _upload(client, visitors_xlsx, "visitors.xlsx")

    overview = client.get("/api/dashboard/overview?preset=all_time").json()
    keys = {k["key"] for k in overview["kpis"]}
    assert {"net_follower_growth", "impressions", "unique_visitors"} <= keys

    content = client.get("/api/dashboard/content?preset=all_time").json()
    assert len(content["posts"]) >= 1
    assert content["posts"][0]["impressions"] >= content["posts"][-1]["impressions"]


def test_newest_upload_wins(client):
    v1 = build_xlsx([["Date", "Total followers"], ["01/15/2024", "100"]])
    v2 = build_xlsx([["Date", "Total followers"], ["01/15/2024", "999"]])
    _upload(client, v1, "f1.xlsx")
    _upload(client, v2, "f2.xlsx")
    foll = client.get("/api/dashboard/followers?preset=all_time").json()
    jan15 = [p for p in foll["daily"]["points"] if p["date"] == "2024-01-15"]
    assert jan15 and jan15[0]["value"] == 999.0
