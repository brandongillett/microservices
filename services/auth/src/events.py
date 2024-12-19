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
from libs.utils_lib.events import event_exists, logger, mark_event_processed, retry_task

rabbit_router = RabbitRouter()


# Subscriber events
async def _process_update_user_username_event(
    session: async_session_dep, data: UpdateUserUsernameEvent
) -> None:
    """
    Logic to update a user's username.

    Args:
        session: The database session.
        data: The event containing the user details to be updated.
    """
    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.username = data.new_username
    session.add(user)
    await session.commit()
    await session.refresh(user)


@rabbit_router.subscriber("update_user_username")
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

    try:
        await retry_task(
            lambda: _process_update_user_username_event(session, data),
            retries=5,
            delay=2,
        )
    except Exception as e:
        logger.error(f"Failed to process event {data.event_id}: {str(e)}")
        # Event to revert the user creation for auth service (will be implemented in the future)

    await mark_event_processed(data.event_id)


async def _process_update_user_password_event(
    session: async_session_dep, data: UpdateUserPasswordEvent
) -> None:
    """
    Logic to update a user's password.

    Args:
        session: The database session.
        data: The event containing the user details to be updated.
    """
    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.password = data.new_password
    session.add(user)
    await session.commit()
    await session.refresh(user)


@rabbit_router.subscriber("update_user_password")
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

    try:
        await retry_task(
            lambda: _process_update_user_password_event(session, data),
            retries=5,
            delay=2,
        )
    except Exception as e:
        logger.error(f"Failed to process event {data.event_id}: {str(e)}")
        # Event to revert the user creation for auth service (will be implemented in the future)

    await mark_event_processed(data.event_id)


async def _process_update_user_role_event(
    session: async_session_dep, data: UpdateUserRoleEvent
) -> None:
    """
    Logic to update a user's role.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """
    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.role = data.new_role
    session.add(user)
    await session.commit()
    await session.refresh(user)


@rabbit_router.subscriber("update_user_role")
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

    try:
        await retry_task(
            lambda: _process_update_user_role_event(session, data), retries=5, delay=2
        )
    except Exception as e:
        logger.error(f"Failed to process event {data.event_id}: {str(e)}")
        # Event to revert the user creation for auth service (will be implemented in the future)

    await mark_event_processed(data.event_id)


# Publisher events
async def create_user_event(user: Users) -> None:
    """
    Publishes an event to create a user

    Args:
        user (User): The user to create.
    """

    event_id = uuid4()

    event = CreateUserEvent(user=user, event_id=event_id)

    await rabbitmq.broker.publish(event, queue="create_user")
