from uuid import UUID

from pydantic import BaseModel

from libs.users_lib.models import UserBase, Users


# User schemas
class UserPublic(UserBase):
    id: UUID


# Event schemas
class CreateUserEvent(BaseModel):
    user: Users
    event_id: UUID


class UpdateUserUsernameEvent(BaseModel):
    event_id: UUID
    user_id: UUID
    new_username: str


class UpdateUserPasswordEvent(BaseModel):
    event_id: UUID
    user_id: UUID
    new_password: str


class UpdateUserRoleEvent(BaseModel):
    event_id: UUID
    user_id: UUID
    new_role: str
