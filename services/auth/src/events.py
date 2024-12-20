from uuid import uuid4

from faststream.rabbit.fastapi import RabbitRouter
from sqlmodel.ext.asyncio.session import AsyncSession

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
from libs.utils_lib.events import event_exists, logger, mark_event_processed

rabbit_router = RabbitRouter()


# Subscriber events
@rabbit_router.subscriber("update_user_username", retry=10)
async def update_user_username_event(
    session: async_session_dep, data: UpdateUserUsernameEvent
) -> None:
    """
    Subscribes to an event to update a user's username.

    Args:
        session: The database session.
        data: The event containing the user details to be updated.
    """
    if await event_exists(data.event_id):
        logger.info(f"Event {data.event_id} already processed.")
        return

    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.username = data.new_username
    session.add(user)
    await session.commit()
    await session.refresh(user)

    await mark_event_processed(data.event_id)


@rabbit_router.subscriber("update_user_password", retry=10)
async def update_user_password_event(
    session: async_session_dep, data: UpdateUserPasswordEvent
) -> None:
    """
    Subscribes to an event to update a user's password.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """
    if await event_exists(data.event_id):
        logger.info(f"Event {data.event_id} already processed.")
        return

    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.password = data.new_password
    session.add(user)
    await session.commit()
    await session.refresh(user)

    await mark_event_processed(data.event_id)


@rabbit_router.subscriber("update_user_role", retry=10)
async def update_user_role_event(
    session: async_session_dep, data: UpdateUserRoleEvent
) -> None:
    """
    Subscribes to an event to update a user's role.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """
    if await event_exists(data.event_id):
        logger.info(f"Event {data.event_id} already processed.")
        return

    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.role = data.new_role
    session.add(user)
    await session.commit()
    await session.refresh(user)

    await mark_event_processed(data.event_id)


# Publisher events
async def create_root_user_event(session: AsyncSession, user: Users) -> None:
    """
    Publishes an event to create a user

    Args:
        user (User): The user to create.
    """
    _ = session  # will use later for outbox

    await rabbitmq.broker.publish(user, queue="create_root_user")


async def create_user_event(session: AsyncSession, user: Users) -> None:
    """
    Publishes an event to create a user

    Args:
        user (User): The user to create.
    """
    _ = session  # will use later for outbox

    event_id = uuid4()

    event = CreateUserEvent(user=user, event_id=event_id)

    await rabbitmq.broker.publish(event, queue="create_user")
