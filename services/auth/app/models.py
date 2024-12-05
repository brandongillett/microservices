from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from shared_lib.models import Users

from app.core.security import security_settings


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
    user: Users = Relationship(back_populates="refresh_tokens")
