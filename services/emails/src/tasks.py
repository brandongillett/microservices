from email.message import EmailMessage
from email.utils import formataddr
from typing import Any

import aiosmtplib
from pydantic_settings import BaseSettings
from taskiq import PrometheusMiddleware, TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq_redis import RedisStreamBroker

from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.faststream import nats
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.core.taskiq import result_backend, schedule_source
from libs.utils_lib.tasks import (
    handle_run_task,
    rerun_persistent_jobs,
    resend_outbox_events,
)
from src.core.config import settings


# Tasks Settings
class tasks_settings(BaseSettings):
    def get_jobs(self) -> dict[str, Any]:
        return {
            "resend_outbox_events": {
                "function": resend_outbox_events_task,
                "cron": "*/5 * * * *",
                "persistent": False,
            },
            "rerun_persistent_jobs": {
                "function": rerun_persistent_jobs_task,
                "cron": "* * * * *",
                "persistent": False,
            },
            # This job will only execute once after 20 minutes
            # "one-time-task": {
            #     "function": test,
            #     "time": datetime.utcnow() + timedelta(minutes=1),
            #     "args": [True],
            #     "kwargs": {"test": "test"},
            #     "persistent": True,  # rerun if missed or failed
            # },
        }

    JOBS = property(get_jobs)


tasks_settings = tasks_settings()  # type: ignore

broker = (
    RedisStreamBroker(utils_lib_settings.REDIS_URL)
    .with_result_backend(result_backend)
    .with_middlewares(
        PrometheusMiddleware(server_addr="0.0.0.0", server_port=9000),
    )
)

scheduler = TaskiqScheduler(broker, sources=[schedule_source])


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    _ = state  # Unused variable
    await session_manager.init_db()
    await redis_client.connect()
    await nats.start()


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    _ = state  # Unused variable
    await session_manager.close()
    await redis_client.close()
    await nats.close()


@broker.task
async def rerun_persistent_jobs_task(job_name: str | None = None) -> None:
    """
    Task to rerun persistent jobs.

    Args:
        job_name (str | None): The name of the job. If provided, the job will be updated.
    """
    async with session_manager.get_session() as session:
        await handle_run_task(
            session,
            "rerun_persistent_jobs_task",
            job_name,
            rerun_persistent_jobs,
            session,
        )


@broker.task
async def resend_outbox_events_task(job_name: str | None = None) -> None:
    """
    Task to resend outbox events.

    Args:
        job_name (str | None): The name of the job. If provided, the job will be updated.
    """
    async with session_manager.get_session() as session:
        await handle_run_task(
            session,
            "resend_outbox_events_task",
            job_name,
            resend_outbox_events,
            session,
        )


@broker.task
async def send_email(email_to: str, subject: str, html: str) -> str:
    """
    Sends an email.

    Args:
        email (str): The email to send the message to.
        subject (str): The subject of the email.
        html (str): The HTML content of the email.
    """
    if utils_lib_settings.ENVIRONMENT in ["local", "staging"] and email_to.endswith(
        "@test-account.com"
    ):
        return "Email sending skipped for test account"

    message = EmailMessage()
    message["From"] = formataddr(
        (settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL)
    )
    message["To"] = email_to
    message["Subject"] = subject
    message.set_content(html, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_TLS,
            username=settings.SMTP_USER if settings.SMTP_USER else None,
            password=settings.SMTP_PASSWORD if settings.SMTP_PASSWORD else None,
        )
        return "Email sent successfully"
    except aiosmtplib.SMTPException as e:
        return f"Failed to send email: {e}"
