from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from libs.users_lib.models import Users
from libs.utils_lib.models import EventInbox, EventOutbox

__all__ = ["Users", "EventInbox", "EventOutbox"]


# Base models
class RefreshTokenBase(SQLModel):
    created: datetime
    expires: datetime
    last_used: datetime
    ip_address: str


# Database models
class RefreshTokens(RefreshTokenBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    refresh_jti: UUID = Field(index=True, unique=True)
    access_jti: UUID
