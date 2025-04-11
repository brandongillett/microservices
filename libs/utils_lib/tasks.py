import importlib
from collections.abc import Callable
from datetime import datetime
from typing import cast

from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.taskiq import logger, schedule_source
from libs.utils_lib.crud import (
    get_failed_outbox_events,
    get_job_by_name,
    get_pending_outbox_events,
    get_persistent_failed_jobs,
    get_persistent_missed_jobs,
)
from libs.utils_lib.models import Jobs, JobStatus


# Job Scheduler Functionality
async def schedule_jobs(jobs: dict) -> None:
    """
    Schedules jobs based on the provided configuration.

    Args:
        jobs (dict): A dictionary containing job configurations.
            Each job should have a 'function', 'cron' or 'time', and optional 'persistent', 'args', 'kwargs'.
    """

    for job_name, config in jobs.items():
        function = config.get("function")
        cron = cast(str | None, config.get("cron"))
        time = cast(int | None, config.get("time"))
        args = config.get("args", {})
        kwargs = config.get("kwargs", {})
        persistent = config.get("persistent", False)

        if cron:
            await (
                function.kicker()
                .with_labels(job_name=job_name, persistent=persistent)
                .schedule_by_cron(schedule_source, cron, **args, **kwargs)
            )
        elif time:
            await (
                function.kicker()
                .with_labels(job_name=job_name, persistent=persistent)
                .schedule_by_time(schedule_source, time, **args, **kwargs)
            )


async def update_job_status(
    session, job: Jobs, status: JobStatus, error: str | None = None
) -> None:
    """
    Helper function to update job status after running.

    Args:
        session: The database session.
        job: The job to update.
        status: The new status for the job.
        error: Optional error message to log if the job failed.
    """
    if job.time:
        if not job.persistent or status == JobStatus.completed:
            job.enabled = False

    job.last_run_status = status
    job.last_run = datetime.utcnow()
    job.last_run_error = error

    await session.commit()
    await session.refresh(job)


# Shared Tasks
async def handle_run_task(
    session: AsyncSession,
    task_name: str,
    job_name: str | None,
    task_function: Callable,
    *args,
    **kwargs,
) -> None:
    """
    Helper function to run a task and update its status if job_name is provided.

    Args:
        session (AsyncSession): The database session.
        task_name (str): The name of the task.
        job_name (str | None): The name of the job.
        task_function (Callable): The function to run.
        *args: Positional arguments for the job logic.
        **kwargs: Keyword arguments for the job logic.
    """
    job = None
    if job_name:
        job = await get_job_by_name(session, job_name)
    try:
        await task_function(*args, **kwargs)
        if job:
            await update_job_status(session, job, JobStatus.completed)
    except Exception as e:
        logger.error(f"Error running {task_name}: {e}")
        if job:
            await update_job_status(session, job, JobStatus.failed, str(e))


async def rerun_persistent_jobs(session: AsyncSession) -> None:
    """
    Rerun persistent jobs that were missed or failed.

    Args:
        session (AsyncSession): The database session.
    """

    """
    We want to rerun jobs where persistent is True &&
    last_run_status == failed

    also we want to rerun jobs where persistent is True &&

    """

    try:
        missed_jobs = await get_persistent_missed_jobs(session)
    except Exception:
        logger.error("Error fetching missed jobs")
        return

    try:
        failed_jobs = await get_persistent_failed_jobs(session)
    except Exception:
        logger.error("Error fetching failed jobs")
        return

    # Combine and deduplicate jobs by job.id
    jobs_by_id = {}
    for job in missed_jobs + failed_jobs:
        jobs_by_id[job.id] = job

    for job in jobs_by_id.values():
        try:
            module_name, function_name = job.task_name.split(":")
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            await function.kiq(**job.args, **job.kwargs)
        except Exception:
            logger.error(f"Error rerunning job {job.job_name}")


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
