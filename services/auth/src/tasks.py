from typing import cast

from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq_redis import RedisAsyncResultBackend, RedisScheduleSource, RedisStreamBroker

from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.crud import get_job_by_name
from libs.utils_lib.tasks import (
    logger,
    resend_outbox_events,
    schedule_new_job,
    update_existing_job,
)

result_backend = RedisAsyncResultBackend(utils_lib_settings.REDIS_URL)  # type: ignore

broker = RedisStreamBroker(utils_lib_settings.REDIS_URL).with_result_backend(
    result_backend
)

redis_source = RedisScheduleSource(utils_lib_settings.REDIS_URL)


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
async def resend_outbox_events_task() -> None:
    """
    Task to resend outbox events.
    """
    await resend_outbox_events()


JOBS = {
    "resend_outbox_events": {
        "function": resend_outbox_events_task,
        "cron": "* * * * *",
    },
    # "interval": {
    #     "function": test_interval_task,
    #     "interval": 5, # Executes in 5 minutes (One time)
    # },
}


async def schedule_jobs() -> None:
    """
    Entry point to schedule all jobs.
    """
    async with session_manager.get_session() as session:
        for job_name, config in JOBS.items():
            function = config.get("function")
            interval = cast(int | None, config.get("interval"))
            cron = cast(str | None, config.get("cron"))
            if not function or (not interval and not cron):
                logger.warning(f"Job {job_name} is misconfigured. Skipping.")
                continue

            lock_key = f"lock:{job_name}"

            if not await redis_client.acquire_lock(lock_key, expiration=20):
                continue

            job = await get_job_by_name(session, job_name)
            redis = await redis_client.get_client()

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
