from uuid import uuid4

from faststream.rabbit.fastapi import RabbitRouter

from libs.users_lib.crud import get_user
from libs.users_lib.models import Users
from libs.users_lib.schemas import (
    CreateUserEvent,
    UpdateUserPasswordEvent,
    UpdateUserRoleEvent,
    UpdateUserUsernameEvent,
)
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.core.rabbitmq import rabbitmq

rabbit_router = RabbitRouter()


# Subscriber events
@rabbit_router.subscriber("update_user_username")
async def update_user_username_event(
    session: async_session_dep, data: UpdateUserUsernameEvent
) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    user = await get_user(session, data.user_id)

    if user:
        user.username = data.new_username
        session.add(user)
        await session.commit()
        await session.refresh(user)


@rabbit_router.subscriber("update_user_password")
async def update_user_password_event(
    session: async_session_dep, data: UpdateUserPasswordEvent
) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    user = await get_user(session, data.user_id)

    if user:
        user.password = data.new_password
        session.add(user)
        await session.commit()
        await session.refresh(user)


@rabbit_router.subscriber("update_user_role")
async def update_user_role_event(
    session: async_session_dep, data: UpdateUserRoleEvent
) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    user = await get_user(session, data.user_id)

    if user:
        user.role = data.new_role
        session.add(user)
        await session.commit()
        await session.refresh(user)


# Publisher events
async def create_user_event(user: Users) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """

    event_id = uuid4()

    event = CreateUserEvent(user=user, event_id=event_id)

    await rabbitmq.broker.publish(event, queue="create_user")
