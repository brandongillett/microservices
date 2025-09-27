from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel

from src.models import RefreshTokenBase


# Token schemas
class Token(SQLModel):
    access_token: str
    token_type: str


# User schemas
class UserCreate(SQLModel):
    username: str
    email: str
    password: str


# Refresh token schemas
class RefreshTokenCreate(SQLModel):
    jti: UUID
    user_id: UUID
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime
    ip_address: str


class RefreshTokenPublic(RefreshTokenBase):
    id: UUID
    user_id: UUID


class RefreshTokensPublic(SQLModel):
    refresh_tokens: list[RefreshTokenPublic]
    count: int


# Password reset schemas
class ResetPassword(SQLModel):
    token: str
    new_password: str
