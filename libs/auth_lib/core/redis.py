from libs.utils_lib.core.config import settings
from libs.utils_lib.core.redis import RedisClient

redis_tokens_client = RedisClient(redis_url=settings.REDIS_TOKENS_URL)
