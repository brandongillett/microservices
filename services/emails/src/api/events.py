from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue
from faststream.rabbit.fastapi import RabbitRouter
from sqlmodel import delete

from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    logger,
)
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.models import EventInbox, EventOutbox

rabbit_router = RabbitRouter()


# Exchanges
@rabbit_router.subscriber(
    RabbitQueue(name="cleanup_database_users", durable=True),
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


# Publisher events
