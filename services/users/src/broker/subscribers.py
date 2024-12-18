from faststream.rabbit.fastapi import RabbitRouter

from src.crud import create_user
from libs.users_lib.models import Users
from libs.utils_lib.api.deps import async_session_dep


rabbit_router = RabbitRouter()

@rabbit_router.subscriber("create_user")
async def create_user_event(session: async_session_dep, user: Users) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    await create_user(session, user)