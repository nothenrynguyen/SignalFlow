"""
Pydantic schemas for event ingestion and validation.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from datetime import datetime
import uuid

EVENT_TYPES = Literal[
    "page_view", "click", "signup", "purchase", "session_start"
]


class EventCreate(BaseModel):
    event_type: str = Field(
        ...,
        description="One of: page_view, click, signup, purchase, session_start",
    )
    user_id: Optional[str] = Field(None, max_length=128)
    session_id: str = Field(..., min_length=1, max_length=128)
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class EventRead(BaseModel):
    id: uuid.UUID
    event_type: str
    user_id: Optional[str]
    session_id: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_event(cls, evt: Any) -> "EventRead":
        """Map ORM field event_metadata → schema field metadata."""
        return cls(
            id=evt.id,
            event_type=evt.event_type,
            user_id=evt.user_id,
            session_id=evt.session_id,
            timestamp=evt.timestamp,
            metadata=evt.event_metadata,
        )
