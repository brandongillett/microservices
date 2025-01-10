from uuid import UUID

from libs.users_lib.models import UserBase, Users
from libs.utils_lib.schemas import EventMessageBase


# User schemas
class UserPublic(UserBase):
    id: UUID


# Event schemas
class CreateUserEvent(EventMessageBase):
    user: Users


class UpdateUserUsernameEvent(EventMessageBase):
    user_id: UUID
    new_username: str


class UpdateUserPasswordEvent(EventMessageBase):
    user_id: UUID
    new_password: str


class UpdateUserRoleEvent(EventMessageBase):
    user_id: UUID
    new_role: str
