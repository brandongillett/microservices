from src.main import rabbit_broker
from src.crud import create_user
from libs.users_lib.models import Users

@rabbit_broker.subscriber("create_user")
async def create_user(user: Users) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    await create_user(user)