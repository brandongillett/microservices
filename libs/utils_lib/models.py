from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


# Base models
class EventInboxBase(SQLModel):
    event_type: str = Field(max_length=255)
    data: dict = Field(default={}, sa_column=Column(JSON))
    processed: bool = Field(default=False)
    retries: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    error_message: str | None = None


class EventOutboxBase(SQLModel):
    event_type: str = Field(max_length=255)
    data: dict = Field(default={}, sa_column=Column(JSON))
    published: bool = Field(default=False)
    retries: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: datetime | None = None
    error_message: str | None = None


# Database models
class EventInbox(EventInboxBase, table=True):
    id: UUID = Field(primary_key=True)


class EventOutbox(EventOutboxBase, table=True):
    id: UUID = Field(primary_key=True)
