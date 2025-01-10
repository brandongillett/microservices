import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from faststream.rabbit.fastapi import RabbitRouter
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.crud import (
    create_inbox_event,
    create_outbox_event,
    get_inbox_event,
    get_outbox_event,
)
from libs.utils_lib.models import ProcessedState
from libs.utils_lib.schemas import AcknowledgementEvent
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rabbit_router = RabbitRouter()


@rabbit_router.subscriber(f"{settings.SERVICE_NAME}_acknowledgements")
async def ack_event(session: async_session_dep, ack: AcknowledgementEvent) -> None:
    """
    Subscribes to an event to handle acknowledgements.

    Args:
        session: The database session.
        acknowledgement: The acknowledgement event.
    """
    try:
        event = await get_outbox_event(session, ack.event_id)
    except Exception as e:
        logger.error(f"Error fetching event: {ack.event_id}: {str(e)}")
        return

    if not event:
        logger.error(f"Event not found for acknowledgement: {ack.event_id}")
        return

    if event.processed == ProcessedState.processed:
        logger.info(f"Acknowledgement already processed for event: {ack.event_id}")
        return

    event.processed = ack.processed

    if ack.processed == ProcessedState.processed:
        event.processed_at = ack.processed_at
    elif ack.processed == ProcessedState.failed:
        event.error_message = ack.error_message

    await session.commit()


async def send_ack(
    event_id: UUID,
    service: str,
    processed_state: ProcessedState,
    processed_at: datetime | None = None,
    error_message: str | None = None,
) -> None:
    """
    Sends an acknowledgement to the event publisher.

    Args:
        event_id: The unique identifier of the event.
        service: The service that processed the event.
        processed_state: The state of the event processing.
        processed_at: The timestamp when the event was processed.
    """
    await rabbitmq.broker.publish(
        AcknowledgementEvent(
            event_id=event_id,
            processed=processed_state,
            processed_at=processed_at,
            error_message=error_message,
        ),
        queue=f"{service}_acknowledgements",
    )


async def handle_subscriber_event(
    session: AsyncSession,
    event_id: UUID,
    event_type: str,
    process_fn: Callable,
    data: Any,
) -> None:
    """
    Handles common logic for processing events, including retries, error handling, and event creation.

    Args:
        session: The database session.
        event_id: Unique identifier for the event.
        event_type: Type of the event.
        process_fn: The function to process the event.
        data: The event data payload.
    """
    # Try to get the event from the inbox
    try:
        event = await get_inbox_event(session, event_id)
    except Exception as e:
        # Log the error and send a failed acknowledgement to the publisher
        log = f"Error fetching event: {event_id} - {str(e)}"

        logger.error(log)

        await send_ack(
            event_id=event_id,
            service=data.service,
            processed_state=ProcessedState.failed,
            error_message=log,
        )

        return

    # If the event has already been processed, send an acknowledgement to the publisher
    if event and event.processed == ProcessedState.processed:
        await send_ack(
            event_id=event_id,
            service=data.service,
            processed_state=ProcessedState.processed,
            processed_at=event.processed_at,
        )
        return

    if not event:
        data_json = data.model_dump(mode="json")
        event = await create_inbox_event(session, event_id, event_type, data_json)
    else:
        event.retries += 1

    processed_state = ProcessedState.pending
    processed_at = None
    error_message = None

    try:
        await process_fn(session, data)

        event.processed = ProcessedState.processed
        event.processed_at = datetime.utcnow()

        processed_state = ProcessedState.processed
        processed_at = event.processed_at
    except Exception as e:
        log = f"Error processing event: {event_id} - {str(e)}"

        logger.error(log)

        event.processed = ProcessedState.failed
        event.error_message = log

        processed_state = ProcessedState.failed
        error_message = log

    await session.commit()

    await send_ack(
        event_id=event_id,
        service=data.service,
        processed_state=processed_state,
        processed_at=processed_at,
        error_message=error_message,
    )


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

    event = await create_outbox_event(
        session=session, event_id=event_id, event_type=event_type, data=event_data
    )

    try:
        await rabbitmq.broker.publish(event_schema, queue=event_type, persist=True)
    except Exception as e:
        log = f"Error publishing event: {event_id} - {str(e)}"

        logger.error(log)

        event.processed = ProcessedState.failed
        event.error_message = log

        await session.commit()
