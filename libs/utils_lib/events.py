import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.crud import create_inbox_event, create_outbox_event, get_inbox_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class event_settings(BaseSettings):
    MAX_RETRIES: int = 20


event_settings = event_settings()


async def handle_subscriber_event(
    session: AsyncSession,
    event_id: UUID,
    event_type: str,
    process_fn: Callable,
    data: Any,
):
    """
    Handles common logic for processing events, including retries, error handling, and event creation.

    Args:
        session: The database session.
        event_id: Unique identifier for the event.
        event_type: Type of the event.
        process_fn: The function to process the event.
        data: The event data payload.

    Returns:
        None
    """
    event = await get_inbox_event(session, event_id)

    if event and event.processed:
        logger.info(f"Event {event_id} already processed.")
        return

    if not event:
        data_json = data.model_dump(mode="json")
        event = await create_inbox_event(session, event_id, event_type, data_json)
    else:
        event.retries += 1
        await session.commit()

        if event.retries > event_settings.MAX_RETRIES:
            logger.warning(f"Event {event_id} reached maximum retries. Abandoning.")
            event.error_message = "Event reached maximum retries."
            await session.commit()
            return

    try:
        await process_fn(session, data)
        event.processed = True
        event.processed_at = datetime.utcnow()
        await session.commit()
    except Exception as e:
        logger.error(f"Error processing event {event_id}: {str(e)}")
        event.error_message = str(e)
        # await session.rollback()
        await session.commit()


async def handle_publish_event(
    session: AsyncSession, event_type: str, event_schema: BaseModel
) -> None:
    """
    Handles the publishing of events to RabbitMQ.

    Args:
        session: The database session.
        event_type: The type of the event.
        event_schema: The event schema containing event data.
    """
    event_id = event_schema.event_id
    event_data = event_schema.model_dump(mode="json")

    # Create an outbox event in the database
    event = await create_outbox_event(
        session=session, event_id=event_id, event_type=event_type, data=event_data
    )

    # Publish the event to RabbitMQ
    try:
        await rabbitmq.broker.publish(event_schema, queue=event_type)
        event.published = True
        event.published_at = datetime.utcnow()
        await session.commit()
    except Exception as e:
        logger.error(f"Error publishing event: {event_id}")
        event.error_message = str(e)
        await session.commit()
