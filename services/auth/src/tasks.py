from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq_redis import RedisAsyncResultBackend, RedisScheduleSource, RedisStreamBroker

from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.crud import create_job, get_job_by_name
from libs.utils_lib.tasks import resend_outbox_events

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


#
JOBS = {
    "resend_outbox_events": {
        "function": resend_outbox_events_task,
        "cron": "* * * * *",
    },
}


async def schedule_jobs() -> None:
    """
    Schedule tasks to be executed.
    """
    print("Attempting to schedule jobs...")
    async with session_manager.get_session() as session:
        for job_name, config in JOBS.items():
            function = config["function"]
            cron = config["cron"]
            lock = await redis_client.acquire_lock(f"lock:{job_name}", expiration=20)

            if lock:
                # Check if the job already exists in the database
                job = await get_job_by_name(
                    session=session,
                    job_name=job_name,
                )
                if job:
                    print(
                        f"Job {job_name} already exists in the database. Skipping creation."
                    )
                else:
                    schedule = await function.schedule_by_cron(
                        redis_source,
                        cron,
                    )
                    job = await create_job(
                        session=session,
                        schedule_id=schedule.schedule_id,
                        job_name=job_name,
                        cron=cron,
                    )

                    # print(f"Scheduled task {job_name} with ID {task_id}")

            else:
                print(f"Lock already acquired for {job_name}. Skipping scheduling.")

            await redis_client.release_lock(f"lock:{job_name}")
