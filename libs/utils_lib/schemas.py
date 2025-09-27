from datetime import datetime
from uuid import UUID

from faststream.nats import JStream, PullSub
from sqlmodel import Field, SQLModel

from libs.utils_lib.models import EventStatus
from src.core.config import settings


# Base models
class EventRoute(SQLModel):
    service: str
    name: str
    stream_name: str = Field(default=settings.SERVICE_NAME + "_STREAM")

    @property
    def subject(self) -> str:
        return f"{self.service}.{self.name}"

    @property
    def pull_sub(self) -> PullSub:
        return PullSub(batch=False)

    @property
    def durable(self) -> str:
        return f"{self.service}.{self.name}".replace(".", "_") + "_durable"

    @property
    def queue(self) -> str:
        return f"{self.service}_{self.name.replace('.', '_')}"

    @property
    def stream(self) -> JStream:
        return JStream(name=self.stream_name, declare=False)

    def subject_for(self, target_service: str) -> str:
        return f"{target_service}.{self.name}"


class EventMessageBase(SQLModel):
    event_id: UUID
    service: str = Field(default=settings.SERVICE_NAME)


# Event acknowledgement model
class AcknowledgementEvent(EventMessageBase):
    status: EventStatus
    processed_at: datetime | None = None
    error_message: str | None = None


# Message model
class Message(SQLModel):
    message: str
