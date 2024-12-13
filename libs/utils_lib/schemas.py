from sqlmodel import SQLModel


# Message model
class Message(SQLModel):
    message: str
