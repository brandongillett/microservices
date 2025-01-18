from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue
from faststream.rabbit.fastapi import RabbitRouter
from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.schemas import CreateUserEmailEvent
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    handle_subscriber_event,
    logger,
)
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.models import EventInbox, EventOutbox
from src.models import UserEmails

rabbit_router = RabbitRouter()


# Exchanges
@rabbit_router.subscriber(
    RabbitQueue(name="cleanup_database_users"),
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
        statement = delete(EventOutbox)
        await session.execute(statement)
        statement = delete(EventInbox)
        await session.execute(statement)
        await session.commit()


# Subscriber events
@rabbit_router.subscriber(RabbitQueue(name="create_user_email", durable=True))
async def create_user_email_event(
    session: async_session_dep, data: CreateUserEmailEvent
) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """

    async def process_create_user(
        session: AsyncSession, data: CreateUserEmailEvent
    ) -> None:
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
        event_type="create_user_email",
        process_fn=process_create_user,
        data=data,
    )


# Publisher events
