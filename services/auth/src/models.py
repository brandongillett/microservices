from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from libs.users_lib.models import Users
from libs.utils_lib.models import EventInbox, EventOutbox, Jobs

__all__ = ["Users", "EventInbox", "EventOutbox", "Jobs"]


# Base models
class RefreshTokenBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    ip_address: str = Field(max_length=45, nullable=False)


# Database models
class RefreshTokens(RefreshTokenBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    jti: UUID = Field(index=True, unique=True)
