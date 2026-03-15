"""
Pydantic schemas for metrics API responses.
"""
from pydantic import BaseModel
from typing import List


class EventTypeCounts(BaseModel):
    event_type: str
    count: int


class MetricsSummary(BaseModel):
    total_events: int
    unique_sessions: int
    unique_users: int
    counts_by_type: List[EventTypeCounts]


class TimeseriesPoint(BaseModel):
    bucket: str  # ISO timestamp string, e.g. "2026-03-14T10:00:00Z"
    count: int


class MetricsTimeseries(BaseModel):
    data: List[TimeseriesPoint]
