from uuid import UUID

from sqlmodel import SQLModel

from libs.auth_lib.models import UserBase


# Token schemas
class TokenData(SQLModel):
    user_id: UUID
    role: str


# User schemas
class UserPublic(UserBase):
    id: UUID


# Message model
class Message(SQLModel):
    message: str
