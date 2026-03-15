"""
Background worker — async post-ingest processing.

run_post_ingest_tasks() is called from the POST /events route after a
successful DB write.  It runs concurrently with the HTTP response so
the caller is never blocked by metric recomputation or WS fanout.

Current tasks:
  1. Invalidate the Redis summary cache so the next /metrics/summary
     call returns fresh data.
  2. Compute an up-to-date summary and broadcast it over WebSocket so
     connected dashboards refresh without needing to poll.
"""
import asyncio

from services.metrics_service import get_summary, invalidate_summary_cache
from websocket.manager import manager


async def run_post_ingest_tasks(db) -> None:
    """
    Fire-and-forget coroutine spawned after each event ingest.
    Errors are caught so they never bubble up to the HTTP response.
    """
    try:
        await invalidate_summary_cache()

        # Recompute summary and push the full payload to WS clients so
        # the frontend can update KPI cards without an extra round-trip.
        summary = await get_summary(db)
        await manager.broadcast({
            "type": "metrics_update",
            "data": summary.model_dump(),
        })
    except Exception as exc:  # noqa: BLE001
        # Log but never crash the worker
        print(f"[worker] post-ingest task error: {exc}")
