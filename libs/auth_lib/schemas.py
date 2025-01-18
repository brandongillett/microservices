from typing import Literal
from uuid import UUID

from sqlmodel import SQLModel

from libs.users_lib.models import Users
from libs.utils_lib.schemas import EventMessageBase


# Token schemas
class TokenData(SQLModel):
    user_id: UUID
    role: str
    type: Literal["access", "refresh"]


# Event schemas
class CreateUserEvent(EventMessageBase):
    user: Users


class CreateUserEmailEvent(EventMessageBase):
    user: Users


class VerifyUserEmailEvent(EventMessageBase):
    user_id: UUID
