from uuid import UUID

from libs.users_lib.models import UserBase


# User schemas
class UserPublic(UserBase):
    id: UUID
