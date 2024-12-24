from datetime import datetime
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
from libs.utils_lib.crud import create_inbox_event, create_outbox_event, get_inbox_event
from libs.utils_lib.events import logger

rabbit_router = RabbitRouter()


# Subscriber events
@rabbit_router.subscriber("update_user_username", retry=True)
async def update_user_username_event(
    session: async_session_dep, data: UpdateUserUsernameEvent
) -> None:
    """
    Subscribes to an event to update a user's username.

    Args:
        session: The database session.
        data: The event containing the user details to be updated.
    """
    event = await get_inbox_event(session, data.event_id)
    event_type = "update_user_username"

    if event and event.processed:
        logger.info(f"Event {data.event_id} already processed.")
        return

    if not event:
        data_json = data.model_dump(mode="json")
        event = await create_inbox_event(session, data.event_id, event_type, data_json)
    else:
        event.retries += 1
        await session.commit()

    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.username = data.new_username
    session.add(user)
    await session.commit()
    await session.refresh(user)

    event.processed = True
    event.processed_at = datetime.utcnow()
    await session.commit()


@rabbit_router.subscriber("update_user_password", retry=True)
async def update_user_password_event(
    session: async_session_dep, data: UpdateUserPasswordEvent
) -> None:
    """
    Subscribes to an event to update a user's password.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """
    event = await get_inbox_event(session, data.event_id)
    event_type = "update_user_password"

    if event and event.processed:
        logger.info(f"Event {data.event_id} already processed.")
        return

    if not event:
        data_json = data.model_dump(mode="json")
        event = await create_inbox_event(session, data.event_id, event_type, data_json)
    else:
        event.retries += 1
        await session.commit()

    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.password = data.new_password
    session.add(user)
    await session.commit()
    await session.refresh(user)

    event.processed = True
    event.processed_at = datetime.utcnow()
    await session.commit()


@rabbit_router.subscriber("update_user_role", retry=True)
async def update_user_role_event(
    session: async_session_dep, data: UpdateUserRoleEvent
) -> None:
    """
    Subscribes to an event to update a user's role.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """
    event = await get_inbox_event(session, data.event_id)
    event_type = "update_user_role"

    if event and event.processed:
        logger.info(f"Event {data.event_id} already processed.")
        return

    if not event:
        data_json = data.model_dump(mode="json")
        event = await create_inbox_event(session, data.event_id, event_type, data_json)
    else:
        event.retries += 1
        await session.commit()

    user = await get_user(session, data.user_id)

    if not user:
        logger.error(f"User {data.user_id} not found.")
        return

    user.role = data.new_role
    session.add(user)
    await session.commit()
    await session.refresh(user)

    event.processed = True
    event.processed_at = datetime.utcnow()
    await session.commit()


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
    event_type = "create_user"
    event_schema = CreateUserEvent(event_id=event_id, user=user)

    event_data = event_schema.model_dump(mode="json")

    event = await create_outbox_event(
        session=session, event_id=event_id, event_type=event_type, data=event_data
    )

    try:
        await rabbitmq.broker.publish(event_schema, queue=event_type)
        event.published = True
        event.published_at = datetime.utcnow()
        await session.commit()
    except Exception as e:
        logger.error(f"Error publishing event: {event_id}")
        event.error_message = str(e)
        await session.commit()
