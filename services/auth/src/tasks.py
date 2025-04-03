from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq_redis import RedisAsyncResultBackend, RedisScheduleSource, RedisStreamBroker

from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.tasks import resend_outbox_events

result_backend = RedisAsyncResultBackend(
    redis_url=utils_lib_settings.REDIS_URL,
)
broker = RedisStreamBroker(utils_lib_settings.REDIS_URL).with_result_backend(
    result_backend
)

redis_source = RedisScheduleSource(utils_lib_settings.REDIS_URL)


scheduler = TaskiqScheduler(broker, sources=[redis_source])


async def schedule_tasks() -> None:
    """
    Schedule tasks to be executed.
    """
    await resend_outbox_events_task.schedule_by_cron(
        redis_source,
        "* * * * *",
    )


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
