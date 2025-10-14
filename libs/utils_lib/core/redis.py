import logging
from typing import Any

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from libs.utils_lib.core.config import settings as utils_lib_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def connect(self) -> None:
        """
        Initializes the Redis connection.
        """
        try:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                retry_on_timeout=True,
                decode_responses=True,
            )
            if not self._pool:
                raise RedisError("Failed to create Redis connection pool.")

            self._client = Redis(connection_pool=self._pool)
            redis = self.get_client()
            await redis.ping()
            logger.info("Successfully established Redis connection.")
        except RedisError as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise

    async def close(self) -> None:
        """
        Closes the Redis connection.
        """
        if self._client:
            await self._client.aclose()
            logger.info("Redis client closed.")
        if self._pool:
            await self._pool.aclose()
            logger.info("Redis connection pool closed.")

    def get_client(self) -> Redis:
        """
        Returns the active Redis client.

        Returns:
            Redis: The active Redis client.
        """
        if self._client is None:
            raise RedisError("Redis client is not initialized or connected.")
        return self._client

    async def ping(self) -> Any:
        """
        Pings the Redis server.

        Returns:
            Any: The response from the Redis server.
        """
        if not self._client:
            raise RedisError("Redis client is not initialized or connected.")
        return await self._client.ping()


redis_client = RedisClient(redis_url=utils_lib_settings.REDIS_URL)
