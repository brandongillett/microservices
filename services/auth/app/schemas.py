from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel

from app.models import RefreshTokenBase


# Token schemas
class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    user_id: UUID


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