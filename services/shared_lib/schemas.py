from uuid import UUID

from sqlmodel import SQLModel

from shared_lib.models import UserBase


# User schemas
class UserPublic(UserBase):
    id: UUID


# Message model
class Message(SQLModel):
    message: str
