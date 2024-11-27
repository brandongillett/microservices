from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

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


class RefreshTokenBase(SQLModel):
    created: datetime
    expires: datetime
    last_used: datetime
    ip_address: str


# Database models
class Users(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password: str
    refresh_tokens: list["RefreshTokens"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )


class RefreshTokens(RefreshTokenBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    refresh_jti: UUID = Field(index=True, unique=True)
    access_jti: UUID
    user: Users = Relationship(back_populates="refresh_tokens")
