import asyncio
import logging
from uuid import UUID

from libs.utils_lib.core.redis import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def retry_task(task, retries: int = 5, delay: int = 2, backoff: bool = True):
    """
    Retries a task with exponential backoff.

    Args:
        task: The task (coroutine) to execute.
        retries (int): Number of retries.
        delay (int): Initial delay in seconds.
        backoff (bool): Whether to use exponential backoff.
    """
    attempt = 0
    while attempt < retries:
        try:
            return await task()
        except Exception as e:
            attempt += 1
            if attempt == retries:
                raise e  # Raise the exception after max retries
            wait_time = delay * (2**attempt if backoff else 1)  # Exponential backoff
            logger.error(f"Error: {e}, retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)


async def mark_event_processed(event_id: UUID) -> None:
    """
    Mark an event as processed.

    Args:
        event_id (UUID): The event to mark as processed.
    """
    client = await redis_client.get_client()
    await client.set(f"{str(event_id)}_processed", "true")


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
