from typing import List
import logging

from redis.asyncio import Redis
from taskiq import ScheduleSource
from taskiq.exceptions import ScheduledTaskCancelledError
from taskiq.scheduler.scheduled_task import ScheduledTask
from sqlmodel import delete, select
from taskiq_redis import RedisAsyncResultBackend, RedisScheduleSource
from sqlmodel.ext.asyncio.session import AsyncSession
from croniter import croniter
from datetime import datetime

from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.redis import RedisClient, redis_client
from libs.utils_lib.core.database import DatabaseSessionManager, session_manager
from libs.utils_lib.models import Jobs
from libs.utils_lib.crud import create_job, get_jobs, get_job_by_name


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Extend the RedisScheduleSource to add a lock mechanism (For distributed scheduling)
class LockScheduleSource(RedisScheduleSource):
    async def pre_send(self, task: ScheduledTask) -> None:
        async with Redis(connection_pool=self.connection_pool) as redis_client:
            lock = await redis_client.set(
                f"schedule_lock:{task.schedule_id}", "lock", nx=True, ex=20
            )
            if not lock:
                raise ScheduledTaskCancelledError()

class MyScheduleSource(ScheduleSource):
    """
    Source of schedules for redis.

    This class allows you to store schedules in redis.
    Also it supports dynamic schedules.

    :param url: url to redis.
    :param prefix: prefix for redis schedule keys.
    :param buffer_size: buffer size for redis scan.
        This is how many keys will be fetched at once.
    :param max_connection_pool_size: maximum number of connections in pool.
    :param serializer: serializer for data.
    :param connection_kwargs: additional arguments for redis BlockingConnectionPool.
    """

    def __init__(
        self,
        session_manager: DatabaseSessionManager,
        redis_client: RedisClient,
    ) -> None:
        self.session_manager = session_manager
        self.redis_client = redis_client


    async def startup(self) -> None:
        await self.session_manager.init_db()
        await self.redis_client.connect()

    async def shutdown(self) -> None:

        await self.session_manager.shutdown()
        await self.redis_client.close()
        
    async def delete_schedule(self, schedule_id: str) -> None:

        async with self.session_manager.get_session() as session:
            statement = delete(Jobs).where(Jobs.schedule_id == schedule_id)
            await session.execute(statement)
            await session.commit()

    async def update_schedule(
        self,
        session: AsyncSession,
        job: Jobs,
        task_name: str,
        next_run: datetime,
        args: dict,
        kwargs: dict,
        labels: dict,
        persistent: bool,
        cron: str | None = None,
        interval: int | None = None,
    ) -> None:
        job.task_name = task_name
        job.next_run = next_run
        job.modified_at = datetime.utcnow()
        job.args = args
        job.kwargs = kwargs
        job.labels = labels
        job.persistent = persistent
        job.cron = cron
        job.interval = interval

        await session.commit()
        await session.refresh(job)


    async def add_schedule(self, schedule: ScheduledTask) -> None:

        async with self.session_manager.get_session() as session:
            if not schedule.labels["job_name"]:
                raise ValueError("Label 'job_name' is required")
            
            job_name = schedule.labels.get("job_name")
            persistent = schedule.labels.get("persistent", False)

            redis = await self.redis_client.get_client()

            lock_key = f"lock:{job_name}"
            lock = await redis.set(lock_key, "lock", nx=True, ex=30)

            if not lock:
                logger.warning(f"Failed to acquire lock for job {job_name}. Skipping.")
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
                    and existing_job.interval == schedule.time
                    and existing_job.persistent == persistent
                ):
                    await redis.delete(lock_key)
                    logger.info(f"Job {job_name} already exists. Skipping creation.")
                    return
                else:
                    # Update the existing job
                    await self.update_schedule(
                        session=session,
                        job=existing_job,
                        task_name=schedule.task_name,
                        next_run=next_run,
                        args=schedule.args,
                        kwargs=schedule.kwargs,
                        labels=schedule.labels,
                        persistent=persistent,
                        cron=schedule.cron,
                        interval=schedule.time,
                    )
                    logger.info(f"Job {existing_job.job_name} updated.")
            else:
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
                    interval=schedule.time,
                    persistent=persistent,
                    commit=True,
                )
                logger.info(f"Job {job_name} created and scheduled.")

            await redis.delete(lock_key)


    async def get_schedules(self) -> List[ScheduledTask]:
        async with self.session_manager.get_session() as session:
            jobs = await get_jobs(session=session)

        schedules = []
        for job in jobs:
            schedule = ScheduledTask(
                schedule_id=job.id,
                task_name=job.task_name,
                args=job.args,
                kwargs=job.kwargs,
                labels=job.labels,
                cron=job.cron,
                time=job.next_run,
            )
            schedules.append(schedule)

        return schedules

    async def post_send(self, task: ScheduledTask) -> None:
        pass


result_backend = RedisAsyncResultBackend(utils_lib_settings.REDIS_URL)

redis_source = MyScheduleSource(session_manager= session_manager, redis_client=redis_client)
