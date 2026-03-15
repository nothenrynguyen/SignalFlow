import asyncio

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.event import EventCreate, EventRead
from services import event_service
from services.worker import run_post_ingest_tasks

router = APIRouter()


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a single activity event.

    The event is written to Postgres synchronously so we can return its
    ID in the response.  Post-ingest work (cache invalidation, metric
    recomputation, WebSocket broadcast) runs as a background task so it
    never adds latency to the HTTP response.
    """
    event = await event_service.create_event(db, payload)
    event_read = EventRead.from_orm_event(event)

    # Spawn background work without blocking the response.
    # Pass the serialised event so the worker can broadcast it to the live feed.
    asyncio.create_task(run_post_ingest_tasks(db, event_read.model_dump()))

    return event_read
