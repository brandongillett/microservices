import logging
from typing import Any

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from app.core.config import settings

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
            logger.info("Successfully established redis connection.")
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


# Initialize the Redis client
redis_client = RedisClient(redis_url=settings.REDIS_URL)
