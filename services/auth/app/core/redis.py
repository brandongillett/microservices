from app.core.config import settings
from libs.utils_lib.core.redis import RedisClient

# Initialize the Redis client
redis_client = RedisClient(redis_url=settings.REDIS_URL)
