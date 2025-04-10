from datetime import datetime, timedelta
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.models import EventInbox, EventOutbox, EventStatus, Jobs, JobStatus


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


# CRUD operations for Tasks
async def create_job(
    session: AsyncSession,
    id: str | None,
    job_name: str,
    next_run: datetime,
    task_name: str,
    args: dict,
    kwargs: dict,
    labels: dict,
    cron: str | None = None,
    time: datetime | None = None,
    persistent: bool = False,
    commit: bool = True,
) -> Jobs:
    """
    Create a job record.

    Args:
        session (AsyncSession): The database session.
        schedule_id (str): The schedule ID.
        job_name (str): The function name.
        cron (str): The cron expression.
        time (datetime): The time to run the job.
        commit (bool): Commit at the end of the operation.

    Returns:
        EventOutbox: The job record.
    """
    job = Jobs(
        id=id,
        job_name=job_name,
        next_run=next_run,
        cron=cron,
        time=time,
        task_name=task_name,
        args=args,
        kwargs=kwargs,
        labels=labels,
        persistent=persistent,
    )
    session.add(job)

    if commit:
        await session.commit()
        await session.refresh(job)

    return job


async def delete_job(
    session: AsyncSession,
    id: str,
    commit: bool = True,
) -> None:
    """
    Delete a job record.

    Args:
        session (AsyncSession): The database session.
        id (str): The job ID.
        commit (bool): Commit at the end of the operation.
    """
    stmt = select(Jobs).where(Jobs.id == id)
    result = await session.exec(stmt)
    job = result.one_or_none()

    if job:
        await session.delete(job)

        if commit:
            await session.commit()


async def get_jobs(session: AsyncSession, get_enabled: bool = False) -> list[Jobs]:
    """
    Get all jobs.

    Args:
        session (AsyncSession): The database session.

    Returns:
        list[Jobs]: The list of jobs.
    """
    if get_enabled:
        stmt = select(Jobs).where(Jobs.enabled.is_(True))
    else:
        stmt = select(Jobs)
    result = await session.exec(stmt)
    return result.all()


async def get_job_by_name(session: AsyncSession, job_name: str) -> Jobs | None:
    """
    Get a job record by name.

    Args:
        session (AsyncSession): The database session.
        job_name (str): The job name.

    Returns:
        Jobs: The job record or None.
    """
    stmt = select(Jobs).where(Jobs.job_name == job_name)
    result = await session.exec(stmt)
    return result.one_or_none()


async def get_persistent_failed_jobs(
    session: AsyncSession,
) -> list[Jobs]:
    """
    Get all persistent failed jobs. If time is provided, get all persistent failed jobs older than the given time in minutes.

    Args:
        session (AsyncSession): The database session.
        time (int): The time in minutes.

    Returns:
        list[Jobs]: The list of persistent failed jobs.
    """
    stmt = select(Jobs).where(
        Jobs.enabled.is_(True),
        Jobs.persistent.is_(True),
        Jobs.last_run_status == JobStatus.failed,
    )
    result = await session.exec(stmt)
    return result.all()


async def get_persistent_missed_jobs(
    session: AsyncSession,
) -> list[Jobs]:
    """
    Get all persistent missed jobs.

    Args:
        session (AsyncSession): The database session.

    Returns:
        list[Jobs]: The list of persistent missed jobs.
    """

    stmt = select(Jobs).where(
        Jobs.enabled.is_(True),
        Jobs.persistent.is_(True),
        Jobs.last_run is not None,
        Jobs.next_run < datetime.utcnow(),
        Jobs.last_run < Jobs.next_run,
    )

    result = await session.exec(stmt)
    return result.all()
