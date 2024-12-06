from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.core.security import security_settings



# Base models
class UserBase(SQLModel):
    username: str = Field(
        unique=True,
        index=True,
        min_length=security_settings.USERNAME_MIN_LENGTH,
        max_length=security_settings.USERNAME_MAX_LENGTH,
    )
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    created: datetime = Field(default_factory=datetime.utcnow)
    disabled: bool = False
    role: str = Field(default="user")