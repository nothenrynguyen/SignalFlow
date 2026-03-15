from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.metrics import MetricsSummary, MetricsTimeseries
from services import metrics_service

router = APIRouter()


@router.get("/summary", response_model=MetricsSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """
    Return aggregate metrics: total events, unique sessions/users,
    and per-type counts.  Results are served from Redis cache (10 s TTL)
    to keep latency low under high ingest load.
    """
    return await metrics_service.get_summary(db)


@router.get("/timeseries", response_model=MetricsTimeseries)
async def get_timeseries(
    interval: str = Query("hour", description="Bucketing interval: minute | hour | day"),
    lookback_hours: int = Query(24, ge=1, le=168, description="How many hours of history to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return time-bucketed event counts suitable for rendering a line chart.
    """
    return await metrics_service.get_timeseries(db, interval=interval, lookback_hours=lookback_hours)
