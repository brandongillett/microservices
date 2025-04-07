import logging
from datetime import datetime, timedelta
from typing import cast

from croniter import croniter
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
from libs.utils_lib.models import Jobs, JobStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Job Configuration
class JobConfig:
    def __init__(self, config: dict) -> None:
        self.function = config.get("function")
        self.interval = cast(int | None, config.get("interval"))
        self.cron = cast(str | None, config.get("cron"))
        self.args = config.get("args", {})
        self.persistent = config.get("persistent", False)

    def compare(self, job: Jobs) -> bool:
        """
        Compare the job configuration with an existing job.

        Args:
            job (Jobs): The existing job to compare against.

        Returns:
            bool: True if the configurations match, False otherwise.
        """
        return (
            # self.function == job.function and
            self.args == job.ARGS
            and self.cron == job.cron
            and self.interval == job.interval
            and self.persistent == job.persistent
        )

    def is_valid(self) -> bool:
        """
        Validate the job configuration.
        Checks if either cron or interval is provided.

        Returns:
            bool: True if valid, False otherwise.
        """
        if self.function is None:
            return False
        if self.interval is not None and self.cron is not None:
            return False
        if self.interval is None and self.cron is None:
            return False

        return True


#
# Job Scheduler Functionality
async def schedule_jobs(jobs: dict, redis_source: RedisScheduleSource) -> None:
    """
    Entry point to schedule all jobs.
    """
    async with session_manager.get_session() as session:
        for job_name, config in jobs.items():
            # Extract job configuration
            job_config = JobConfig(config)

            # Validate job configuration
            if not job_config.is_valid():
                logger.warning(f"Job {job_name} is misconfigured. Skipping.")
                continue

            # Check if the job already exists in the database
            job = await get_job_by_name(session, job_name)
            redis = await redis_client.get_client()

            if job:
                scheduled = await redis.exists(f"schedule:{job.schedule_id}")
                if scheduled and job_config.compare(job):
                    logger.info(f"Job {job_name} already scheduled. Skipping...")
                    continue

            # Try to acquire a lock for the job
            lock_key = f"lock:{job_name}"
            if not await redis_client.acquire_lock(lock_key):
                logger.warning(f"Failed to acquire lock for job {job_name}. Skipping.")
                continue

            if job:
                await update_existing_job(
                    session=session,
                    job=job,
                    function=job_config.function,
                    args=job_config.args,
                    cron=job_config.cron,
                    interval=job_config.interval,
                    persistent=job_config.persistent,
                    redis_source=redis_source,
                )

            else:
                await schedule_new_job(
                    session=session,
                    job_name=job_name,
                    function=job_config.function,
                    args=job_config.args,
                    cron=job_config.cron,
                    interval=job_config.interval,
                    persistent=job_config.persistent,
                    redis_source=redis_source,
                )

            await redis_client.release_lock(lock_key)


async def schedule_new_job(
    session: AsyncSession,
    job_name: str,
    function: callable,
    args: dict,
    cron: str | None,
    interval: int | None,
    persistent: bool,
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
    next_run = datetime.utcnow()
    if interval:
        schedule = await function.schedule_by_time(
            redis_source, datetime.utcnow() + timedelta(minutes=interval), **args
        )
        next_run = next_run + timedelta(minutes=interval)
    else:
        schedule = await function.schedule_by_cron(redis_source, cron, **args)
        cron_next_run = croniter(cron, next_run)
        next_run = cron_next_run.get_next(datetime)

    await create_job(
        session=session,
        schedule_id=schedule.schedule_id,
        job_name=job_name,
        next_run=next_run,
        cron=cron,
        interval=interval,
        args=args,
        persistent=persistent,
    )
    logger.info(f"Job {job_name} created and scheduled.")


async def update_existing_job(
    session: AsyncSession,
    job: Jobs,
    function: callable,
    args: dict,
    cron: str | None,
    interval: int | None,
    persistent: bool,
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

    next_run = datetime.utcnow()
    if interval:
        schedule = await function.schedule_by_time(
            redis_source, datetime.utcnow() + timedelta(minutes=interval), **args
        )
        next_run = next_run + timedelta(minutes=interval)
    else:
        schedule = await function.schedule_by_cron(redis_source, cron, **args)
        cron_next_run = croniter(cron, next_run)
        next_run = cron_next_run.get_next(datetime)

    job.schedule_id = schedule.schedule_id
    job.modified_at = datetime.utcnow()
    job.next_run = next_run
    job.ARGS = args
    job.persistent = persistent
    job.cron = cron
    job.interval = interval

    await session.commit()
    await session.refresh(job)

    logger.info(f"Job {job.job_name} updated.")


async def update_job_status(
    session, job: Jobs, status: JobStatus, error: str | None = None
) -> None:
    """
    Updates the job's status, last run time, and error message (if any).

    Args:
        session: The database session.
        job: The job to update.
        status: The new status for the job.
        error: Optional error message to log if the job failed.
    """
    if job.interval:
        job.next_run = datetime.utcnow() + timedelta(seconds=job.interval)
    else:
        cron_next_run = croniter(job.cron, datetime.utcnow())
        job.next_run = cron_next_run.get_next(datetime)

    job.last_run_status = status
    job.last_run = datetime.utcnow()
    job.last_run_error = error
    await session.commit()
    await session.refresh(job)


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
