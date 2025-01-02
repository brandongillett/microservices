import logging

from sqlmodel import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from libs.utils_lib.core.database import DatabaseSessionManager
from libs.utils_lib.core.rabbitmq import RabbitMQ
from libs.utils_lib.core.redis import RedisClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def test_db_connection(session_manager: DatabaseSessionManager) -> None:
    """
    Tests the database connection by executing a simple query.

    Args:
        session_manager (DatabaseSessionManager): The database session manager instance.
    """
    try:
        await session_manager.init_db()

        if not session_manager.session_maker:
            raise Exception("Database session manager not initialized.")
        async with session_manager.session_maker() as session:
            await session.exec(select(1))

        await session_manager.close()
    except Exception as e:
        logger.error(e)
        raise e


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def test_redis_connection(redis_client: RedisClient) -> None:
    """
    Tests the Redis connection using the ping method.

    Args:
        redis_client (RedisClient): The Redis client instance.
    """
    try:
        await redis_client.connect()

        if not await redis_client.ping():
            raise Exception("Could not reach redis.")

        await redis_client.close()
    except Exception as e:
        logger.error(e)
        raise e


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def test_rabbitmq_connection(rabbitmq_client: RabbitMQ) -> None:
    """
    Tests the RabbitMQ connection by declaring a queue.

    Args:
        rabbitmq_client (rabbitmq): The RabbitMQ client instance.
    """
    try:
        await rabbitmq_client.start()

        await rabbitmq_client.close()
    except Exception as e:
        logger.error(e)
        raise e
