from uuid import UUID

from pydantic import EmailStr
from sqlmodel import SQLModel

from shared_lib.models import UserBase


# User schemas
class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str

class UserPublic(UserBase):
    id: UUID

# Message model
class Message(SQLModel):
    message: str