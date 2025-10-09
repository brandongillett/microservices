import logging
from datetime import datetime

from croniter import croniter
from prometheus_client import start_http_server
from taskiq import ScheduleSource
from taskiq.exceptions import ScheduledTaskCancelledError
from taskiq.scheduler.scheduled_task import ScheduledTask
from taskiq_redis import RedisAsyncResultBackend

from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import DatabaseSessionManager, session_manager
from libs.utils_lib.core.redis import RedisClient, redis_client
from libs.utils_lib.crud import create_job, delete_job, get_job_by_name, get_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MyScheduleSource(ScheduleSource):
    """
    Custom schedule source for managing scheduled tasks.

    Args:
        session_manager (DatabaseSessionManager): The database session manager.
        redis_client (RedisClient): The Redis client for distributed locking.
    """

    def __init__(
        self,
        session_manager: DatabaseSessionManager,
        redis_client: RedisClient,
    ) -> None:
        self.session_manager = session_manager
        self.redis_client = redis_client
        self.prometheus_server = None
        self.prometheus_thread = None

    async def startup(self) -> None:
        """
        Initialize the schedule source.
        """
        # Start Prometheus metrics server on port 9000
        self.prometheus_server, self.prometheus_thread = start_http_server(9000)
        # Initialize database and Redis connections
        await self.session_manager.init_db()
        await self.redis_client.connect()

    async def shutdown(self) -> None:
        """
        Shutdown the schedule source.
        """
        # Shutdown Prometheus metrics server
        self.prometheus_server.shutdown()
        self.prometheus_thread.join()
        # Close database and Redis connections
        await self.session_manager.close()
        await self.redis_client.close()

    async def delete_schedule(self, schedule_id: str) -> None:
        """
        Delete a schedule.

        Args:
            schedule_id (str): The schedule ID.
        """
        async with self.session_manager.get_session() as session:
            await delete_job(
                session=session,
                id=schedule_id,
                commit=True,
            )

    async def add_schedule(self, schedule: ScheduledTask) -> None:
        """
        Add a schedule.

        Args:
            schedule (ScheduledTask): The schedule to add.
        """
        async with self.session_manager.get_session() as session:
            if not schedule.labels["job_name"]:
                raise ValueError("Label 'job_name' is required")

            job_name = schedule.labels.get("job_name")
            persistent = schedule.labels.get("persistent", False)
            if isinstance(persistent, str):
                persistent = persistent.lower() == "true"

            redis = self.redis_client.client

            lock_key = f"lock:add_schedule:{schedule.schedule_id}"
            lock = await redis.set(lock_key, "lock", nx=True, ex=30)

            if not lock:
                logger.info(
                    f"Job {job_name} is already being scheduled by another instance. Skipping..."
                )
                return

            # Add the job name to the schedule kwargs
            schedule.kwargs.update({"job_name": job_name})

            # Calculate the next run time
            next_run = schedule.time
            if schedule.cron:
                cron_next_run = croniter(schedule.cron, datetime.utcnow())
                next_run = cron_next_run.get_next(datetime)

            # Check if the job already exists
            existing_job = await get_job_by_name(session=session, job_name=job_name)

            if existing_job:
                if (
                    existing_job.task_name == schedule.task_name
                    and existing_job.args == schedule.args
                    and existing_job.kwargs == schedule.kwargs
                    and existing_job.cron == schedule.cron
                    and existing_job.time == schedule.time
                    and existing_job.persistent == persistent
                ):
                    await redis.delete(lock_key)
                    logger.info(f"Job {job_name} already exists. Skipping creation.")
                    return
                else:
                    await delete_job(
                        session=session,
                        id=existing_job.id,
                        commit=True,
                    )

            await create_job(
                session=session,
                id=schedule.schedule_id,
                job_name=job_name,
                next_run=next_run,
                task_name=schedule.task_name,
                args=schedule.args,
                kwargs=schedule.kwargs,
                labels=schedule.labels,
                cron=schedule.cron,
                time=schedule.time,
                persistent=persistent,
                commit=True,
            )
            if existing_job:
                logger.info(f"Job {job_name} updated.")
            else:
                logger.info(f"Job {job_name} created.")

            await redis.delete(lock_key)

    async def get_schedules(self) -> list[ScheduledTask]:
        """
        Get all schedules.

        Returns:
            list[ScheduledTask]: List of schedules.
        """
        async with self.session_manager.get_session(read_only=True) as session:
            jobs = await get_jobs(session=session, get_enabled=True)

        schedules = []
        for job in jobs:
            schedule = ScheduledTask(
                schedule_id=job.id,
                task_name=job.task_name,
                args=job.args,
                kwargs=job.kwargs,
                labels=job.labels,
                cron=job.cron,
                time=job.time,
            )
            schedules.append(schedule)

        return schedules

    async def pre_send(self, task: ScheduledTask) -> None:
        """
        Pre-send hook for scheduled tasks.

        Args:
            task (ScheduledTask): The scheduled task.
        """
        redis = self.redis_client.client
        lock = await redis.set(
            f"lock:schedule:{task.schedule_id}", "lock", nx=True, ex=30
        )
        if not lock:
            logger.info(
                f"Task {task.schedule_id} is already being handled by another instance. Skipping."
            )
            raise ScheduledTaskCancelledError()

    async def post_send(self, task: ScheduledTask) -> None:
        """
        Post-send hook for scheduled tasks.

        Args:
            task (ScheduledTask): The scheduled task.
        """
        if task.cron:
            async with self.session_manager.get_session() as session:
                job = await get_job_by_name(
                    session=session, job_name=task.labels["job_name"]
                )
                cron_next_run = croniter(job.cron, datetime.utcnow())
                job.next_run = cron_next_run.get_next(datetime)

                await session.commit()
                await session.refresh(job)


result_backend = RedisAsyncResultBackend(
    utils_lib_settings.REDIS_URL, result_ex_time=900
)

schedule_source = MyScheduleSource(
    session_manager=session_manager, redis_client=redis_client
)
