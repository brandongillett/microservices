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
        self.pool: ConnectionPool | None = None
        self.client: Redis | None = None

    async def connect(self) -> None:
        """
        Initializes the Redis connection.
        """
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                retry_on_timeout=True,
                decode_responses=True,
            )
            if not self.pool:
                raise RedisError("Failed to create Redis connection pool.")

            self.client = Redis(connection_pool=self.pool)
            await self.client.ping()
            logger.info("Successfully established Redis connection.")
        except RedisError as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise

    async def close(self) -> None:
        """
        Closes the Redis connection.
        """
        if self.client:
            await self.client.close()
            logger.info("Redis client closed.")
        if self.pool:
            await self.pool.aclose()
            logger.info("Redis connection pool closed.")

    async def ping(self) -> Any:
        """
        Pings the Redis server.

        Returns:
            Any: The response from the Redis server.
        """
        if not self.client:
            raise RedisError("No active Redis client found.")
        return await self.client.ping()

    async def acquire_lock(self, lock_name: str, expiration: int = 60) -> bool:
        """
        Acquire a lock in Redis.

        Args:
            lock_name (str): The name of the lock.
            expiration (int): The expiration time for the lock in seconds.

        Returns:
            bool: True if the lock was acquired, False otherwise.
        """
        if not self.client:
            raise RedisError("No active Redis client found.")

        lock = await self.client.set(lock_name, "lock", nx=True, ex=expiration)

        return lock is not None and lock

    async def release_lock(self, lock_name: str) -> None:
        """
        Release a lock in Redis.

        Args:
            lock_name (str): The name of the lock.
        """
        if not self.client:
            raise RedisError("No active Redis client found.")
        await self.client.delete(lock_name)

    async def get_client(self) -> Redis:
        """
        Returns the Redis client, connecting if necessary.

        Returns:
            Redis: The Redis client.
        """
        if self.client is None:
            logger.info("No active Redis client found, attempting to connect...")
            await self.connect()
        if self.client is None:
            raise RedisError("Failed to establish a Redis client connection.")
        return self.client


redis_client = RedisClient(redis_url=utils_lib_settings.REDIS_URL)
