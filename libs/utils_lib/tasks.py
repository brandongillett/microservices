import logging
from datetime import datetime
from typing import cast

from croniter import croniter
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.taskiq import redis_source
from libs.utils_lib.crud import (
    get_failed_outbox_events,
    get_pending_outbox_events,
    get_persistent_failed_jobs,
)
from libs.utils_lib.models import Jobs, JobStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Job Configuration
class JobConfig:
    def __init__(self, config: dict) -> None:
        self.function = config.get("function")
        self.function_name = self.function.__name__.split("__taskiq")[0]
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
            self.function_name == job.function
            and self.args == job.ARGS
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
async def schedule_jobs(jobs: dict) -> None:
    """
    Entry point to schedule all jobs.
    """
    _ = jobs  # Unused variable
    from src import tasks

    await (
        tasks.resend_outbox_events_task.kicker()
        .with_labels(job_name="resend_outbox_events")
        .schedule_by_cron(redis_source, "* * * * *")
    )

    # async with session_manager.get_session() as session:
    #     for job_name, config in jobs.items():
    #         # Extract job configuration
    #         job_config = JobConfig(config)

    #         # Validate job configuration
    #         if not job_config.is_valid():
    #             logger.warning(f"Job {job_name} is misconfigured. Skipping.")
    #             continue

    #         # Check if the job already exists in the database
    #         job = await get_job_by_name(session, job_name)
    #         redis = await redis_client.get_client()

    #         if job:
    #             scheduled = await redis.exists(f"schedule:{job.schedule_id}")
    #             if job_config.cron and scheduled and job_config.compare(job):
    #                 logger.info(f"Job {job_name} already scheduled. Skipping...")
    #                 continue
    #             elif job_config.interval and job_config.compare(job):
    #                 logger.info(f"Job {job_name} already scheduled. Skipping...")
    #                 continue

    #         # Try to acquire a lock for the job
    #         lock_key = f"lock:{job_name}"
    #         lock = await redis.set(lock_key, "lock", nx=True, ex=60)
    #         if not lock:
    #             logger.warning(f"Failed to acquire lock for job {job_name}. Skipping.")
    #             continue

    #         if job:
    #             await update_existing_job(
    #                 session=session,
    #                 job=job,
    #                 function=job_config.function,
    #                 function_name=job_config.function_name,
    #                 args=job_config.args,
    #                 cron=job_config.cron,
    #                 interval=job_config.interval,
    #                 persistent=job_config.persistent,
    #                 redis_source=redis_source,
    #             )

    #         else:
    #             await schedule_new_job(
    #                 session=session,
    #                 job_name=job_name,
    #                 function=job_config.function,
    #                 function_name=job_config.function_name,
    #                 args=job_config.args,
    #                 cron=job_config.cron,
    #                 interval=job_config.interval,
    #                 persistent=job_config.persistent,
    #                 redis_source=redis_source,
    #             )

    #         # Release the lock after scheduling
    #         await redis.delete(lock_key)


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
    if job.cron:
        cron_next_run = croniter(job.cron, datetime.utcnow())
        job.next_run = cron_next_run.get_next(datetime)

    job.last_run_status = status
    job.last_run = datetime.utcnow()
    job.last_run_error = error

    await session.commit()
    await session.refresh(job)


# Shared Tasks
async def rerun_persistent_jobs(session: AsyncSession) -> None:
    """
    Rerun persistent jobs that were missed or failed.

    Args:
        session (AsyncSession): The database session.
    """
    try:
        failed_jobs = await get_persistent_failed_jobs(session)
    except Exception as e:
        logger.error(f"Error fetching persistent jobs: {str(e)}")
        return

    from src import tasks

    for job in failed_jobs:
        function = getattr(tasks, job.function)
        #  Send job to worker queue
        await function.kiq(**job.ARGS)


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
