from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from libs.auth_lib.core.security import security_settings as auth_lib_security_settings


# Base models
class UserBase(SQLModel):
    username: str = Field(
        unique=True,
        index=True,
        min_length=auth_lib_security_settings.USERNAME_MIN_LENGTH,
        max_length=auth_lib_security_settings.USERNAME_MAX_LENGTH,
    )
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    role: str = Field(default="user")
    disabled: bool = False
    verified: bool = False


# Database models
class Users(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password: str
