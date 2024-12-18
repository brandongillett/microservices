from faststream.rabbit.fastapi import RabbitRouter
from libs.users_lib.models import Users

rabbit_router = RabbitRouter()

@rabbit_router.publisher("create_user")
async def create_user_event(user: Users) -> None:
    """
    Publishes a message to create a user.

    Args:
        user (User): The user to create.
    """
    await rabbit_router.publish("create_user", user)
