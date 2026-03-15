"""
Tests for GET /metrics/summary and GET /metrics/timeseries.
"""
import pytest
from unittest.mock import AsyncMock, patch
from schemas.metrics import MetricsTimeseries, TimeseriesPoint


async def _seed(client, count: int = 5):
    """Helper — insert `count` events via the API."""
    for i in range(count):
        etype = ["page_view", "click", "signup"][i % 3]
        await client.post("/events", json={"event_type": etype, "session_id": f"s{i}"})


@pytest.mark.asyncio
async def test_summary_empty_db(client):
    resp = await client.get("/metrics/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_events"] == 0
    assert body["unique_sessions"] == 0
    assert body["counts_by_type"] == []


@pytest.mark.asyncio
async def test_summary_counts_correctly(client):
    await _seed(client, 6)
    resp = await client.get("/metrics/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_events"] == 6
    assert body["unique_sessions"] == 6
    types = {r["event_type"] for r in body["counts_by_type"]}
    assert types == {"page_view", "click", "signup"}


@pytest.mark.asyncio
async def test_summary_unique_sessions(client):
    for _ in range(2):
        await client.post("/events", json={"event_type": "click", "session_id": "shared"})
    await client.post("/events", json={"event_type": "click", "session_id": "other"})

    resp = await client.get("/metrics/summary")
    body = resp.json()
    assert body["total_events"] == 3
    assert body["unique_sessions"] == 2


# ── Timeseries — mock the service to avoid date_trunc (Postgres-only) ─────────

@pytest.mark.asyncio
async def test_timeseries_returns_list(client):
    fake = MetricsTimeseries(data=[
        TimeseriesPoint(bucket="2026-03-14T10:00:00", count=5),
        TimeseriesPoint(bucket="2026-03-14T11:00:00", count=3),
    ])
    with patch("api.metrics.metrics_service.get_timeseries", new=AsyncMock(return_value=fake)):
        resp = await client.get("/metrics/timeseries?interval=hour")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["data"][0]["count"] == 5


@pytest.mark.asyncio
async def test_timeseries_invalid_interval_accepted(client):
    """Router accepts any string; service clamps it — no 422 from FastAPI."""
    fake = MetricsTimeseries(data=[])
    with patch("api.metrics.metrics_service.get_timeseries", new=AsyncMock(return_value=fake)):
        resp = await client.get("/metrics/timeseries?interval=decade")
    assert resp.status_code == 200

