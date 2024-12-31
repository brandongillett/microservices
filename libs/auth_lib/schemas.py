from typing import Literal
from uuid import UUID

from sqlmodel import SQLModel


# Token schemas
class TokenData(SQLModel):
    user_id: UUID
    role: str
    type: Literal["access", "refresh"]
