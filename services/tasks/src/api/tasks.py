import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
from pytz import UTC  # type: ignore

from libs.utils_lib.core.rabbitmq import rabbitmq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

scheduler.configure(
    timezone=UTC,
)

DEFAULT_JOBS = {
    "resend_outbox_events": {"type": "interval", "minutes": 5},
    # "weekly_mon_wed": {"type": "cron", "day_of_week": "mon,wed", "hour": 1, "minute": 30},
}


async def send_rabbitmq_event(job_name: str) -> None:
    """Publish a RabbitMQ message for a given job."""
    try:
        await rabbitmq.broker.publish(exchange=job_name)
    except Exception as e:
        logger.error(f"Failed to send RabbitMQ event for job {job_name}: {e}")


async def start_task_scheduler() -> None:
    """Schedule all tasks"""

    for job_name, config in DEFAULT_JOBS.items():
        trigger = None
        if config["type"] == "interval":
            trigger = IntervalTrigger(
                **{k: v for k, v in config.items() if k != "type"}
            )
        elif config["type"] == "cron":
            trigger = CronTrigger(**{k: v for k, v in config.items() if k != "type"})

        if trigger:
            scheduler.add_job(
                send_rabbitmq_event,
                trigger,
                id=job_name,
                name=job_name.replace("_", " ").title(),
                replace_existing=True,
                kwargs={"job_name": job_name},
                misfire_grace_time=60,
                coalesce=False,
            )
            logger.info(f"Scheduled job '{job_name}' with {config}.")

    # Start scheduler
    scheduler.start()
    logger.info("Task scheduler started.")


async def stop_task_scheduler() -> None:
    """Stop all scheduled tasks"""
    scheduler.shutdown()
