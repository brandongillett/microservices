from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.utils_lib.models import EventInbox, EventOutbox, Jobs

__all__ = ["SQLModel", "EventInbox", "EventOutbox", "Jobs"]


# Base models
class UserEmailsBase(SQLModel):
    username: str = Field(
        unique=True,
        index=True,
        min_length=auth_lib_security_settings.USERNAME_MIN_LENGTH,
        max_length=auth_lib_security_settings.USERNAME_MAX_LENGTH,
    )
    email: str = Field(
        unique=True,
        index=True,
        min_length=auth_lib_security_settings.EMAIL_MIN_LENGTH,
        max_length=auth_lib_security_settings.EMAIL_MAX_LENGTH,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False


# Database models
class UserEmails(UserEmailsBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
