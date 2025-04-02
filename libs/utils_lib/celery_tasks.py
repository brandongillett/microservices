import logging

from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.crud import (
    get_failed_outbox_events,
    get_pending_outbox_events,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def resend_outbox_events() -> None:
    """
    Subscribes to an event to resend failed/pending outbox events.

    """
    async with session_manager.get_session() as session:
        try:
            failed_events = await get_failed_outbox_events(session)
        except Exception as e:
            logger.error(f"Error fetching failed outbox events: {str(e)}")
            return

        for event in failed_events:
            await handle_publish_event(
                session=session, event=event, event_schema=event.data
            )

            event.retries += 1

        await session.commit()

        try:
            pending_events = await get_pending_outbox_events(session, time=10)
        except Exception as e:
            logger.error(f"Error fetching pending outbox events: {str(e)}")
            return

        for event in pending_events:
            await handle_publish_event(
                session=session, event=event, event_schema=event.data
            )

            event.retries += 1

        await session.commit()
