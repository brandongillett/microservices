from datetime import datetime
from uuid import UUID

from pydantic import EmailStr
from sqlmodel import SQLModel

from libs.auth_lib.models import RefreshTokenBase


# Token schemas
class Token(SQLModel):
    access_token: str
    token_type: str


# User schemas
class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str


# Refresh token schemas
class RefreshTokenCreate(SQLModel):
    refresh_jti: UUID
    access_jti: UUID
    user_id: UUID
    created: datetime
    expires: datetime
    last_used: datetime
    ip_address: str


class RefreshTokenPublic(RefreshTokenBase):
    id: UUID
    user_id: UUID


class RefreshTokensPublic(SQLModel):
    refresh_tokens: list[RefreshTokenPublic]
    count: int
