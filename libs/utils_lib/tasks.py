import logging
from datetime import datetime, timedelta
from typing import cast

from sqlmodel.ext.asyncio.session import AsyncSession
from taskiq_redis import RedisScheduleSource

from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.crud import (
    create_job,
    get_failed_outbox_events,
    get_job_by_name,
    get_pending_outbox_events,
)
from libs.utils_lib.models import Jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Job Scheduler Functionality
async def schedule_jobs(jobs: dict, redis_source: RedisScheduleSource) -> None:
    """
    Entry point to schedule all jobs.
    """
    async with session_manager.get_session() as session:
        for job_name, config in jobs.items():
            function = config.get("function")
            interval = cast(int | None, config.get("interval"))
            cron = cast(str | None, config.get("cron"))
            if not function or (not interval and not cron):
                logger.warning(f"Job {job_name} is misconfigured. Skipping.")
                continue

            lock_key = f"lock:{job_name}"

            job = await get_job_by_name(session, job_name)
            redis = await redis_client.get_client()

            if not await redis_client.acquire_lock(lock_key):
                continue

            if job:
                scheduled = await redis.exists(f"schedule:{job.schedule_id}")
                if job.cron == cron and job.interval == interval and scheduled:
                    logger.info(f"Job {job_name} already scheduled. Skipping...")
                    await redis_client.release_lock(lock_key)
                    continue
                await update_existing_job(
                    session=session,
                    job=job,
                    function=function,
                    cron=cron,
                    interval=interval,
                    redis_source=redis_source,
                )
                logger.info(f"Job {job_name} updated.")

            else:
                await schedule_new_job(
                    session=session,
                    job_name=job_name,
                    function=function,
                    cron=cron,
                    interval=interval,
                    redis_source=redis_source,
                )
                logger.info(f"Job {job_name} scheduled.")

            await redis_client.release_lock(lock_key)


async def schedule_new_job(
    session: AsyncSession,
    job_name: str,
    function: callable,
    cron: str | None,
    interval: int | None,
    redis_source: RedisScheduleSource,
) -> None:
    """
    Schedule a new job.

    Args:
        session (AsyncSession): The database session.
        job_name (str): The name of the job.
        function (callable): The function to be scheduled.
        cron (str | None): The cron expression for scheduling.
        interval (int | None): The interval in minutes for scheduling.
        redis_source (RedisScheduleSource): The Redis source for scheduling.
    """
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
    """
    Update an existing job.

    Args:
        session (AsyncSession): The database session.
        job (Jobs): The job to be updated.
        function (callable): The function to be scheduled.
        cron (str | None): The cron expression for scheduling.
        interval (int | None): The interval in minutes for scheduling.
        redis_source (RedisScheduleSource): The Redis source for scheduling.
    """
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


# Shared Tasks
async def resend_outbox_events(session: AsyncSession) -> None:
    """
    Task to resend outbox events.

    Args:
        session (AsyncSession): The database session.
    """
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
