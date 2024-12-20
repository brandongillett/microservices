import logging
from datetime import timedelta
from uuid import UUID

from libs.utils_lib.core.redis import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def mark_event_processed(event_id: UUID) -> None:
    """
    Mark an event as processed.

    Args:
        event_id (UUID): The event to mark as processed.
    """
    client = await redis_client.get_client()
    await client.set(f"{str(event_id)}_processed", "true", ex=timedelta(days=1))


async def event_exists(event_id: UUID) -> bool:
    """
    Check if an event has been processed.

    Args:
        event (str): The event to check.

    Returns:
        bool: True if the event has been processed, False otherwise.
    """
    client = await redis_client.get_client()
    result = await client.get(f"{str(event_id)}_processed")
    return result is not None
