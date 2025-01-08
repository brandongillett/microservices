from uuid import UUID

from sqlmodel import SQLModel


# User schemas
class UpdateUsername(SQLModel):
    new_username: str


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


# Management schemas
class UpdateUserRole(SQLModel):
    new_role: str
