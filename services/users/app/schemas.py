from uuid import UUID

from pydantic import EmailStr
from sqlmodel import SQLModel

from app.models import UserBase


# Token schemas
class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    user_id: UUID


# User schemas
class UserPublic(UserBase):
    id: UUID


class UpdateUsername(SQLModel):
    new_username: str


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str
