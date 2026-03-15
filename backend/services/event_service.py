"""
Event persistence service.
Handles writing validated events to PostgreSQL.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from schemas.event import EventCreate


async def create_event(db: AsyncSession, payload: EventCreate) -> Event:
    """
    Persist a new event row and return the ORM instance.
    If the caller omits timestamp we default to now(UTC).
    """
    event = Event(
        event_type=payload.event_type,
        user_id=payload.user_id,
        session_id=payload.session_id,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
        event_metadata=payload.metadata,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
