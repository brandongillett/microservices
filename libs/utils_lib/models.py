from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


# Processed state enum
class ProcessedState(Enum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


# Base models
class EventBase(SQLModel):
    event_type: str = Field(max_length=255)
    data: dict = Field(default={})
    processed: ProcessedState = Field(default=ProcessedState.pending)
    retries: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    error_message: str | None = None


# Database models
class EventInbox(EventBase, table=True):
    id: UUID = Field(primary_key=True)
    data: dict = Field(default={}, sa_column=Column(JSON))


class EventOutbox(EventBase, table=True):
    id: UUID = Field(primary_key=True)
    data: dict = Field(default={}, sa_column=Column(JSON))
