from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from libs.utils_lib.models import EventInbox, EventOutbox

__all__ = ["SQLModel", "EventInbox", "EventOutbox"]


# Base models
class UserEmailsBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False


# Database models
class UserEmails(UserEmailsBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
