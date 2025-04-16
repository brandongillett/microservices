from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from libs.auth_lib.core.security import security_settings as auth_lib_security_settings


# User Roles Enum
class UserRole(Enum):
    user = "user"
    admin = "admin"
    root = "root"


# Base models
class UserBase(SQLModel):
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
    role: UserRole = Field(default=UserRole.user)
    disabled: bool = False
    verified: bool = False


# Database models
class Users(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password: str
