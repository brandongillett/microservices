from uuid import UUID

from sqlmodel import SQLModel


# Token schemas
class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    user_id: UUID


# User schemas
class UpdateUsername(SQLModel):
    new_username: str


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str
