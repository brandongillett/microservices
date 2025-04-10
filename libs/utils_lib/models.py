from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


# Event Status Enum
class EventStatus(Enum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


# Task Status Enum
class JobStatus(Enum):
    completed = "completed"
    failed = "failed"


# Base models
class EventBase(SQLModel):
    event_type: str = Field(max_length=255)
    data: dict = Field(default={})
    status: EventStatus = Field(default=EventStatus.pending)
    retries: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None


class JobsBase(SQLModel):
    job_name: str = Field(
        unique=True,
        max_length=255,
        index=True,
    )
    cron: str | None = None
    time: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    next_run: datetime
    last_run: datetime | None = None
    persistent: bool = Field(default=False)
    last_run_status: JobStatus | None = Field(default=None)
    enabled: bool = Field(default=True)


# Database models
class EventInbox(EventBase, table=True):
    id: UUID = Field(primary_key=True)
    data: dict = Field(default={}, sa_column=Column(JSON))
    error_message: str | None = Field(default=None, sa_column=Column(Text))


class EventOutbox(EventBase, table=True):
    id: UUID = Field(primary_key=True)
    data: dict = Field(default={}, sa_column=Column(JSON))
    error_message: str | None = Field(default=None, sa_column=Column(Text))


class Jobs(JobsBase, table=True):
    id: str = Field(
        primary_key=True,
        default_factory=lambda: uuid4().hex,
        index=True,
    )
    task_name: str = Field(max_length=255)
    args: dict = Field(default={}, sa_column=Column(JSON))
    kwargs: dict = Field(default={}, sa_column=Column(JSON))
    labels: dict = Field(default={}, sa_column=Column(JSON))
    last_run_error: str | None = Field(default=None, sa_column=Column(Text))
