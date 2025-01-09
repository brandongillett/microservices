from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from libs.utils_lib.models import ProcessedState
from src.core.config import settings


# Base models
class EventBase(SQLModel):
    event_id: UUID
    service: str = Field(default=settings.SERVICE_NAME)


# Event acknowledgement model
class AcknowledgementEvent(EventBase):
    processed: ProcessedState
    processed_at: datetime | None = None
    error_message: str | None = None


# Message model
class Message(SQLModel):
    message: str
