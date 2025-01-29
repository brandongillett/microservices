from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from libs.utils_lib.core.rabbitmq import rabbitmq

scheduler = AsyncIOScheduler()


async def resend_outbox_events() -> None:
    await rabbitmq.broker.publish(exchange="resend_outbox_events")


async def start_task_scheduler() -> None:
    """Schedule all tasks"""

    # Jobs
    scheduler.add_job(
        resend_outbox_events,
        IntervalTrigger(minutes=5),
        id="resend_outbox_events_task",
        name="Resend Outbox Events",
    )

    # Start scheduler
    scheduler.start()


async def stop_task_scheduler() -> None:
    """Stop all scheduled tasks"""
    scheduler.shutdown()
