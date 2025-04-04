import logging
from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession
from taskiq_redis import RedisScheduleSource

from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.crud import (
    create_job,
    get_failed_outbox_events,
    get_pending_outbox_events,
)
from libs.utils_lib.models import Jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Job Scheduler Functionality


async def schedule_new_job(
    session: AsyncSession,
    job_name: str,
    function: callable,
    cron: str | None,
    interval: int | None,
    redis_source: RedisScheduleSource,
) -> None:
    if interval:
        schedule = await function.schedule_by_time(
            redis_source, datetime.utcnow() + timedelta(minutes=interval)
        )
    else:
        schedule = await function.schedule_by_cron(redis_source, cron)

    await create_job(
        session=session,
        schedule_id=schedule.schedule_id,
        job_name=job_name,
        cron=cron,
        interval=interval,
    )
    logger.info(f"Job {job_name} created and scheduled.")


async def update_existing_job(
    session: AsyncSession,
    job: Jobs,
    function: callable,
    cron: str | None,
    interval: int | None,
    redis_source: RedisScheduleSource,
) -> None:
    try:
        await redis_source.delete_schedule(job.schedule_id)
    except Exception:
        logger.warning(f"Job {job} not found in scheduler.")

    if interval:
        schedule = await function.schedule_by_time(
            redis_source, datetime.utcnow() + timedelta(minutes=interval)
        )
    else:
        schedule = await function.schedule_by_cron(redis_source, cron)

    job.schedule_id = schedule.schedule_id
    job.cron = cron
    job.interval = interval
    await session.commit()
    logger.info(f"Job {job.job_name} updated.")


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
