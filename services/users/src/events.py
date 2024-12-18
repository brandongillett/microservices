from faststream.rabbit.fastapi import RabbitRouter

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
    dbObj = Users.model_validate(user)
    session.add(dbObj)
    await session.commit()
    await session.refresh(dbObj)
