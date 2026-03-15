"""
Metrics computation service.
Queries aggregated event data from PostgreSQL and caches results in Redis.
"""
import json
from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from schemas.metrics import EventTypeCounts, MetricsSummary, MetricsTimeseries, TimeseriesPoint
from services.cache import get_redis

SUMMARY_CACHE_KEY = "metrics:summary"
SUMMARY_TTL = 10  # seconds — short TTL keeps the dashboard feeling live


async def get_summary(db: AsyncSession, lookback_hours: float | None = None) -> MetricsSummary:
    """Return aggregate metrics, served from Redis cache when fresh.

    When lookback_hours is provided, the cache is bypassed so the query
    reflects only the requested time window.
    """
    if lookback_hours is not None:
        # Time-filtered queries are not cached — they're cheap and always fresh.
        return await _compute_summary(db, lookback_hours=lookback_hours)

    redis = await get_redis()
    cached = await redis.get(SUMMARY_CACHE_KEY)
    if cached:
        return MetricsSummary.model_validate_json(cached)

    summary = await _compute_summary(db)
    await redis.setex(SUMMARY_CACHE_KEY, SUMMARY_TTL, summary.model_dump_json())
    return summary


async def _compute_summary(db: AsyncSession, lookback_hours: float | None = None) -> MetricsSummary:
    """Run the aggregate queries directly against PostgreSQL."""
    since = (
        datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        if lookback_hours is not None
        else None
    )

    def _since_filter(col):
        return [col >= since] if since is not None else []

    # Total event count
    total_result = await db.execute(
        select(func.count()).select_from(Event).where(*_since_filter(Event.timestamp))
    )
    total_events: int = total_result.scalar_one()

    # Unique sessions
    sessions_result = await db.execute(
        select(func.count(func.distinct(Event.session_id)))
        .where(*_since_filter(Event.timestamp))
    )
    unique_sessions: int = sessions_result.scalar_one()

    # Unique users (non-null only)
    users_result = await db.execute(
        select(func.count(func.distinct(Event.user_id)))
        .where(Event.user_id.isnot(None), *_since_filter(Event.timestamp))
    )
    unique_users: int = users_result.scalar_one()

    # Counts per event type
    type_result = await db.execute(
        select(Event.event_type, func.count().label("count"))
        .where(*_since_filter(Event.timestamp))
        .group_by(Event.event_type)
        .order_by(func.count().desc())
    )
    counts_by_type = [
        EventTypeCounts(event_type=row.event_type, count=row.count)
        for row in type_result
    ]

    return MetricsSummary(
        total_events=total_events,
        unique_sessions=unique_sessions,
        unique_users=unique_users,
        counts_by_type=counts_by_type,
    )


async def get_timeseries(
    db: AsyncSession,
    interval: str = "hour",
    lookback_hours: int = 24,
) -> MetricsTimeseries:
    """
    Return per-bucket event counts for the past `lookback_hours`.
    `interval` must be a valid PostgreSQL date_trunc unit: 'minute', 'hour', 'day'.
    """
    allowed = {"minute", "hour", "day"}
    if interval not in allowed:
        interval = "hour"

    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    bucket_col = func.date_trunc(interval, Event.timestamp).label("bucket")
    result = await db.execute(
        select(bucket_col, func.count().label("count"))
        .where(Event.timestamp >= since)
        .group_by(bucket_col)
        .order_by(bucket_col)
    )

    data = [
        TimeseriesPoint(
            bucket=row.bucket.isoformat(),
            count=row.count,
        )
        for row in result
    ]

    return MetricsTimeseries(data=data)


async def invalidate_summary_cache() -> None:
    """Delete the cached summary so the next request recomputes it."""
    redis = await get_redis()
    await redis.delete(SUMMARY_CACHE_KEY)
