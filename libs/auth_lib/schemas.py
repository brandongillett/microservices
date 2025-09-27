from typing import Literal
from uuid import UUID

from sqlmodel import SQLModel

from libs.users_lib.models import Users
from libs.utils_lib.schemas import EventMessageBase


# Token schemas
class TokenData(SQLModel):
    user_id: UUID
    role: str
    verified: bool
    type: Literal["access", "refresh"]


# Event schemas
class CreateUserEvent(EventMessageBase):
    user: Users


class VerifyUserEvent(EventMessageBase):
    user_id: UUID


class VerificationSendEvent(EventMessageBase):
    user: Users


class ForgotPasswordSendEvent(EventMessageBase):
    user_id: UUID
    token: str
