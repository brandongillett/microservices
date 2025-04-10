from typing import Any

from pydantic_settings import BaseSettings
from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq_redis import RedisStreamBroker

from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.core.taskiq import redis_source, result_backend
from libs.utils_lib.crud import get_job_by_name
from libs.utils_lib.models import JobStatus
from libs.utils_lib.tasks import (
    logger,
    rerun_persistent_jobs,
    resend_outbox_events,
    update_job_status,
)


# Tasks Settings
class tasks_settings(BaseSettings):
    def get_jobs(self) -> dict[str, Any]:
        return {
            # "resend_outbox_events": {
            #     "function": resend_outbox_events_task,
            #     "cron": "* * * * *",
            #     "args": {"job_name": "resend_outbox_events"},
            #     "persistent": False,
            # },
            # "rerun_persistent_jobs": {
            #     "function": rerun_persistent_jobs_task,
            #     "cron": "* * * * *",
            #     "args": {"job_name": "rerun_persistent_jobs"},
            #     "persistent": False,
            # },
            # #This job will only execute once after 20 minutes
            # "one-time-task": {
            #     "function": test,
            #     "interval": 1,
            #     "args": {"job_name": "one-time-task"},
            #     "persistent": True, # rerun if missed or failed
            # },
        }

    JOBS = property(get_jobs)


tasks_settings = tasks_settings()  # type: ignore

broker = RedisStreamBroker(utils_lib_settings.REDIS_URL).with_result_backend(
    result_backend
)

scheduler = TaskiqScheduler(broker, sources=[redis_source])


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    _ = state  # Unused variable
    await session_manager.init_db()
    await redis_client.connect()
    await rabbitmq.start()


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    _ = state  # Unused variable
    await session_manager.close()
    await redis_client.close()
    await rabbitmq.close()


@broker.task
async def test(job_name: str | None = None) -> None:
    """
    Test task to check if the task is working.

    Args:
        job_name (str | None): The name of the job. If provided, the job will be updated.
    """
    async with session_manager.get_session() as session:
        if job_name:
            job = await get_job_by_name(session, job_name)
        try:
            print("THIS IS A TEST: ", job_name)
            if job:
                await update_job_status(session, job, JobStatus.completed)
        except Exception as e:
            logger.error(f"Error running {__name__}: {e}")
            if job:
                await update_job_status(session, job, JobStatus.failed, str(e))


@broker.task
async def rerun_persistent_jobs_task(job_name: str | None = None) -> None:
    """
    Task to rerun persistent jobs.

    Args:
        job_name (str | None): The name of the job. If provided, the job will be updated.
    """
    async with session_manager.get_session() as session:
        if job_name:
            job = await get_job_by_name(session, job_name)
        try:
            await rerun_persistent_jobs(session=session)
            if job:
                await update_job_status(session, job, JobStatus.completed)
        except Exception as e:
            logger.error(f"Error running {__name__}: {e}")
            if job:
                await update_job_status(session, job, JobStatus.failed, str(e))


@broker.task
async def resend_outbox_events_task(job_name: str | None = None) -> None:
    """
    Task to resend outbox events.

    Args:
        job_name (str | None): The name of the job. If provided, the job will be updated.
    """
    async with session_manager.get_session() as session:
        if job_name:
            job = await get_job_by_name(session, job_name)
        try:
            await resend_outbox_events(session=session)
            if job:
                await update_job_status(session, job, JobStatus.completed)
        except Exception as e:
            logger.error(f"Error running {__name__}: {e}")
            if job:
                await update_job_status(session, job, JobStatus.failed, str(e))
