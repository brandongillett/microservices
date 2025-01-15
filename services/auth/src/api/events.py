from uuid import UUID, uuid4

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue
from faststream.rabbit.fastapi import RabbitRouter
from sqlmodel import delete, not_
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.schemas import CreateUserEvent, VerifyUserEmailEvent
from libs.users_lib.crud import get_user, update_user_role, update_user_username
from libs.users_lib.models import Users
from libs.users_lib.schemas import (
    UpdateUserPasswordEvent,
    UpdateUserRoleEvent,
    UpdateUserUsernameEvent,
)
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    handle_publish_event,
    handle_subscriber_event,
    logger,
)
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.models import EventInbox, EventOutbox
from src.models import RefreshTokens

rabbit_router = RabbitRouter()


# Exchanges
@rabbit_router.subscriber(
    RabbitQueue(name="cleanup_database_auth", durable=True),
    RabbitExchange("cleanup_database", type=ExchangeType.FANOUT),
)
async def cleanup_database_event(session: async_session_dep) -> None:
    """
    Subscribes to an event to clean up the database.

    Args:
        session: The database session.
    """
    if utils_lib_settings.ENVIRONMENT == "production":
        logger.error("Cannot clean up database in production.")
        return

    if utils_lib_settings.ENVIRONMENT in ["local", "staging"]:
        statement = delete(RefreshTokens)
        await session.execute(statement)
        statement = delete(Users).where(not_(Users.username == "root"))
        await session.execute(statement)
        statement = delete(EventOutbox)
        await session.execute(statement)
        statement = delete(EventInbox)
        await session.execute(statement)
        await session.commit()


# Subscriber events
@rabbit_router.subscriber(RabbitQueue(name="update_user_username", durable=True))
async def update_user_username_event(
    session: async_session_dep, data: UpdateUserUsernameEvent
) -> None:
    """
    Subscribes to an event to update a user's username.

    Args:
        session: The database session.
        data: The event containing the user details to be updated.
    """

    # Callable function to process the event
    async def process_update_user_username(
        session: AsyncSession, data: UpdateUserUsernameEvent
    ) -> None:
        """
        Processes the logic for updating a user's username.

        Args:
            session: The database session.
            data: The event containing the user details to be updated.

        Returns:
            None
        """
        await update_user_username(session, data.user_id, data.new_username)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type="update_user_username",
        process_fn=process_update_user_username,
        data=data,
    )


@rabbit_router.subscriber(RabbitQueue(name="update_user_password", durable=True))
async def update_user_password_event(
    session: async_session_dep, data: UpdateUserPasswordEvent
) -> None:
    """
    Subscribes to an event to update a user's password.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """

    async def process_update_user_password(
        session: AsyncSession, data: UpdateUserPasswordEvent
    ) -> None:
        """
        Processes the logic for updating a user's password.

        Args:
            session: The database session.
            data: The event containing the user details to be updated.

        Returns:
            None
        """
        user = await get_user(session, data.user_id)

        if not user:
            raise ValueError(f"User {data.user_id} not found.")

        user.password = data.new_password
        session.add(user)
        await session.commit()
        await session.refresh(user)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type="update_user_password",
        process_fn=process_update_user_password,
        data=data,
    )


@rabbit_router.subscriber(RabbitQueue(name="update_user_role", durable=True))
async def update_user_role_event(
    session: async_session_dep, data: UpdateUserRoleEvent
) -> None:
    """
    Subscribes to an event to update a user's role.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """

    async def process_update_user_role(
        session: AsyncSession, data: UpdateUserRoleEvent
    ) -> None:
        """
        Processes the logic for updating a user's role.

        Args:
            session: The database session.
            data: The event containing the user details to be updated.

        Returns:
            None
        """
        await update_user_role(session, data.user_id, data.new_role)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type="update_user_role",
        process_fn=process_update_user_role,
        data=data,
    )


# Publisher events
async def create_root_user_event(user: Users) -> None:
    """
    Publishes an event to create a user

    Args:
        user (User): The user to create.
    """
    await rabbitmq.broker.publish(user, queue="create_root_user")


async def create_user_event(session: AsyncSession, user: Users) -> EventOutbox:
    """
    Publishes an event to create a user

    Args:
        user (User): The user to create.

    Returns:
        EventOutbox: The event outbox record.
    """
    event_schema = CreateUserEvent(event_id=uuid4(), user=user)

    event = await handle_publish_event(
        session=session, event_type="create_user", event_schema=event_schema
    )

    return event


async def verify_user_email_event(session: AsyncSession, user_id: UUID) -> EventOutbox:
    """
    Publishes an event to create a user

    Args:
        user_id (UUID): The user ID.

    Returns:
        EventOutbox: The event outbox record.
    """
    event_schema = VerifyUserEmailEvent(event_id=uuid4(), user_id=user_id)

    event = await handle_publish_event(
        session=session, event_type="verify_user_email", event_schema=event_schema
    )

    return event
