from uuid import UUID

from libs.users_lib.models import UserBase, Users
from libs.utils_lib.schemas import EventBase


# User schemas
class UserPublic(UserBase):
    id: UUID


# Event schemas
class CreateUserEvent(EventBase):
    user: Users


class UpdateUserUsernameEvent(EventBase):
    user_id: UUID
    new_username: str


class UpdateUserPasswordEvent(EventBase):
    user_id: UUID
    new_password: str


class UpdateUserRoleEvent(EventBase):
    user_id: UUID
    new_role: str
