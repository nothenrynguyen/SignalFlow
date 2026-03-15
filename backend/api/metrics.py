from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.metrics import MetricsSummary, MetricsTimeseries
from services import metrics_service

router = APIRouter()


@router.get("/summary", response_model=MetricsSummary)
async def get_summary(
    lookback_hours: float | None = Query(
        None,
        ge=0.1,
        le=168,
        description="Restrict summary to the last N hours. Omit for all-time.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Return aggregate metrics: total events, unique sessions/users,
    and per-type counts.  Results are served from Redis cache (10 s TTL)
    when no time filter is applied.
    """
    return await metrics_service.get_summary(db, lookback_hours=lookback_hours)


@router.get("/timeseries", response_model=MetricsTimeseries)
async def get_timeseries(
    interval: str = Query("hour", description="Bucketing interval: minute | hour | day"),
    lookback_hours: float = Query(24.0, ge=0.1, le=168, description="How many hours of history to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return time-bucketed event counts suitable for rendering a line chart.
    """
    return await metrics_service.get_timeseries(db, interval=interval, lookback_hours=lookback_hours)
