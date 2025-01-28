from datetime import datetime, timedelta
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.models import EventInbox, EventOutbox, EventStatus


# CRUD operations for EventInbox
async def create_inbox_event(
    session: AsyncSession,
    event_id: UUID,
    event_type: str,
    data: dict,
    commit: bool = True,
) -> EventInbox:
    """
    Create an event inbox record.

    Args:
        session (AsyncSession): The database session.
        event_type (str): The event type.
        data (Json): The event data.
        commit (bool): Commit at the end of the operation.

    Returns:
        EventInbox: The event inbox record.
    """
    event_inbox = EventInbox(id=event_id, event_type=event_type, data=data)
    session.add(event_inbox)

    if commit:
        await session.commit()
        await session.refresh(event_inbox)

    return event_inbox


async def get_inbox_event(session: AsyncSession, event_id: UUID) -> EventInbox | None:
    """
    Get an event inbox record by ID.

    Args:
        session (AsyncSession): The database session.
        event_id (UUID): The event ID.

    Returns:
        EventInbox: The event inbox record or None.
    """
    stmt = select(EventInbox).where(EventInbox.id == event_id)
    result = await session.exec(stmt)
    return result.one_or_none()


# CRUD operations for EventOutbox
async def create_outbox_event(
    session: AsyncSession,
    event_id: UUID,
    event_type: str,
    data: dict,
    commit: bool = True,
) -> EventOutbox:
    """
    Create an event outbox record.

    Args:
        session (AsyncSession): The database session.
        event_type (str): The event type.
        data (Json): The event data.
        commit (bool): Commit at the end of the operation.

    Returns:
        EventOutbox: The event outbox record.
    """
    event_outbox = EventOutbox(id=event_id, event_type=event_type, data=data)
    session.add(event_outbox)

    if commit:
        await session.commit()
        await session.refresh(event_outbox)

    return event_outbox


async def get_outbox_event(session: AsyncSession, event_id: UUID) -> EventOutbox | None:
    """
    Get an event outbox record by ID.

    Args:
        session (AsyncSession): The database session.
        event_id (UUID): The event ID.

    Returns:
        EventOutbox: The event outbox record or None.
    """
    stmt = select(EventOutbox).where(EventOutbox.id == event_id)
    result = await session.exec(stmt)
    return result.one_or_none()


async def get_failed_outbox_events(session: AsyncSession) -> list[EventOutbox]:
    """
    Get all failed outbox events.

    Args:
        session (AsyncSession): The database session.

    Returns:
        list[EventOutbox]: The list of failed outbox events.
    """
    stmt = select(EventOutbox).where(EventOutbox.status == EventStatus.failed)
    result = await session.exec(stmt)
    return result.all()


async def get_pending_outbox_events(
    session: AsyncSession, time: int | None
) -> list[EventOutbox]:
    """
    Get all pending outbox events. If time is provided, get all pending outbox events older than the given time in minutes.

    Args:
        session (AsyncSession): The database session.
        time (int): The time in minutes.

    Returns:
        list[EventOutbox]: The list of pending outbox events.
    """
    if time:
        minutes_ago = datetime.utcnow() - timedelta(minutes=time)

        stmt = select(EventOutbox).where(
            EventOutbox.status == EventStatus.pending,
            EventOutbox.created_at < minutes_ago,
        )
    else:
        stmt = select(EventOutbox).where(EventOutbox.status == EventStatus.pending)

    result = await session.exec(stmt)
    return result.all()
