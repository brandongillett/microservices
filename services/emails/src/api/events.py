from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue
from faststream.rabbit.fastapi import RabbitRouter
from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.schemas import CreateUserEvent, VerifyUserEvent
from libs.users_lib.schemas import UpdateUserUsernameEvent
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    handle_subscriber_event,
    logger,
)
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.models import EventInbox, EventOutbox
from src.crud import get_user_by_username, update_user_username, verify_user_email
from src.models import UserEmails

rabbit_router = RabbitRouter()


# Exchanges
@rabbit_router.subscriber(
    RabbitQueue(name="cleanup_database_emails"),
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
    if (
        utils_lib_settings.ENVIRONMENT == "local"
        or utils_lib_settings.ENVIRONMENT == "staging"
    ):
        statement = delete(UserEmails)
        await session.execute(statement)
        statement = delete(EventOutbox)
        await session.execute(statement)
        statement = delete(EventInbox)
        await session.execute(statement)
        await session.commit()


# Subscriber events
@rabbit_router.subscriber("emails_service_create_root_user")
async def create_root_user_event(session: async_session_dep, user: UserEmails) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """
    user_exists = await get_user_by_username(session, user.username)

    if not user_exists:
        dbObj = UserEmails.model_validate(user)
        session.add(dbObj)
        await session.commit()
        await session.refresh(dbObj)
        logger.info("Root user created.")


@rabbit_router.subscriber(RabbitQueue(name="emails_service_create_user", durable=True))
async def create_user_event(
    session: async_session_dep, data: CreateUserEvent
) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """

    async def process_create_user(session: AsyncSession, data: CreateUserEvent) -> None:
        """
        Processes the logic for creating a user.

        Args:
            session: The database session.
            data: The event containing the user details to be created.

        Returns:
            None
        """
        dbObj = UserEmails.model_validate(data.user)
        session.add(dbObj)
        await session.commit()
        await session.refresh(dbObj)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type="emails_service_create_user",
        process_fn=process_create_user,
        data=data,
    )


@rabbit_router.subscriber(
    RabbitQueue(name="emails_service_update_username", durable=True)
)
async def update_username_event(
    session: async_session_dep, data: UpdateUserUsernameEvent
) -> None:
    """
    Subscribes to an event to update a user's username.

    Args:
        session: The database session.
        data: The event containing the user details to be updated.
    """

    # Callable function to process the event
    async def process_update_username(
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
        process_fn=process_update_username,
        data=data,
    )


@rabbit_router.subscriber(RabbitQueue(name="emails_service_verify_user", durable=True))
async def verify_user_event(session: async_session_dep, data: VerifyUserEvent) -> None:
    """
    Subscribes to an event to to verify a user's email.

    Args:
        session: The database session.
        user (User): The user to create.
    """

    async def process_verify_user_event(
        session: AsyncSession, data: VerifyUserEvent
    ) -> None:
        """
        Processes the logic for verifying a user's email.

        Args:
            session: The database session.
            data: The event containing the user details to be created.

        Returns:
            None
        """
        await verify_user_email(session, data.user_id)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type="emails_service_verify_user",
        process_fn=process_verify_user_event,
        data=data,
    )
