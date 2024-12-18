from uuid import UUID

from pydantic import BaseModel

from libs.users_lib.models import UserBase


# User schemas
class UserPublic(UserBase):
    id: UUID


# Event schemas
class UpdateUserUsernameEvent(BaseModel):
    user_id: UUID
    new_username: str


class UpdateUserPasswordEvent(BaseModel):
    user_id: UUID
    new_password: str


class UpdateUserRoleEvent(BaseModel):
    user_id: UUID
    new_role: str
