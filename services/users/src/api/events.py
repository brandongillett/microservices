from datetime import datetime
from uuid import UUID, uuid4

from faststream.rabbit.fastapi import RabbitRouter
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.crud import get_user_by_username
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
@rabbit_router.subscriber("create_root_user", retry=10)
async def create_root_user_event(session: async_session_dep, user: Users) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """
    user_exists = await get_user_by_username(session, user.username)

    if not user_exists:
        dbObj = Users.model_validate(user)
        session.add(dbObj)
        await session.commit()
        await session.refresh(dbObj)
        logger.info("Root user created.")


@rabbit_router.subscriber("create_user", retry=10)
async def create_user_event(session: async_session_dep, data: CreateUserEvent) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """
    event = await get_inbox_event(session, data.event_id)
    event_type = "create_user"

    if event and event.processed:
        logger.info(f"Event {data.event_id} already processed.")
        return

    if not event:
        data_json = data.model_dump(mode="json")
        event = await create_inbox_event(session, data.event_id, event_type, data_json)
    else:
        event.retries += 1
        await session.commit()

    dbObj = Users.model_validate(data.user)
    session.add(dbObj)
    await session.commit()
    await session.refresh(dbObj)

    event.processed = True
    event.processed_at = datetime.utcnow()
    await session.commit()


# Publisher events
async def update_user_username_event(
    session: AsyncSession, user_id: UUID, new_username: str
) -> None:
    """
    Publishes an event to update a user's username.

    Args:
        user_id (UUID): The user's ID.
        new_username (str): The new username.
    """
    event_id = uuid4()
    event_type = "update_user_username"
    event_schema = UpdateUserUsernameEvent(
        event_id=event_id, user_id=user_id, new_username=new_username
    )

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


async def update_user_password_event(
    session: AsyncSession, user_id: UUID, new_password: str
) -> None:
    """
    Publishes a event to update a user's password.

    Args:
        user_id (UUID): The user's ID.
        new_password (str): The new password.
    """
    event_id = uuid4()
    event_type = "update_user_password"
    event_schema = UpdateUserPasswordEvent(
        event_id=event_id, user_id=user_id, new_password=new_password
    )

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


async def update_user_role_event(
    session: AsyncSession, user_id: UUID, new_role: str
) -> None:
    """
    Publishes an event to update a user's role.

    Args:
        user_id (UUID): The user's ID.
        new_role (str): The new role.
    """
    event_id = uuid4()
    event_type = "update_user_role"
    event_schema = UpdateUserRoleEvent(
        event_id=event_id, user_id=user_id, new_role=new_role
    )

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
