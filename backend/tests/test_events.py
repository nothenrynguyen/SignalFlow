"""
Tests for POST /events and GET /health.
"""
import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_event_returns_201(client):
    payload = {
        "event_type": "page_view",
        "session_id": "sess-abc",
        "user_id": "user-1",
    }
    resp = await client.post("/events", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["event_type"] == "page_view"
    assert body["session_id"] == "sess-abc"
    assert "id" in body


@pytest.mark.asyncio
async def test_ingest_event_missing_session_id_returns_422(client):
    resp = await client.post("/events", json={"event_type": "click"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_event_stores_metadata(client):
    payload = {
        "event_type": "purchase",
        "session_id": "sess-xyz",
        "metadata": {"amount": 49.99, "currency": "USD"},
    }
    resp = await client.post("/events", json=payload)
    assert resp.status_code == 201
    assert resp.json()["metadata"]["amount"] == 49.99


@pytest.mark.asyncio
async def test_multiple_events_accepted(client):
    for etype in ["page_view", "click", "signup"]:
        resp = await client.post("/events", json={"event_type": etype, "session_id": "s1"})
        assert resp.status_code == 201
