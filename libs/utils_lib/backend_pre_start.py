import logging

from sqlmodel import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from libs.auth_lib.core.redis import redis_tokens_client
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.redis import RedisClient, redis_client

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
async def test_db_connection() -> None:
    """
    Tests the database connection by executing a simple query.
    """
    try:
        await session_manager.init_db()
        if not session_manager.session_maker:
            raise Exception("Database session manager not initialized.")
        async with session_manager.session_maker() as session:
            await session.exec(select(1))
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
    except Exception as e:
        logger.error(e)
        raise e


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def test_redis_tokens_connection(redis_tokens_client: RedisClient) -> None:
    """
    Tests the Redis Tokens connection using the ping method.

    Args:
        redis_client (RedisClient): The Redis client instance.
    """
    try:
        await redis_tokens_client.connect()
        if not await redis_tokens_client.ping():
            raise Exception("Could not reach redis.")
    except Exception as e:
        logger.error(e)
        raise e


async def initialize_services() -> None:
    """
    Initialize database and Redis services.
    """
    await test_db_connection()
    await session_manager.close()
    await test_redis_connection(redis_client)
    await redis_client.close()
    await test_redis_tokens_connection(redis_tokens_client)
    await redis_tokens_client.close()
