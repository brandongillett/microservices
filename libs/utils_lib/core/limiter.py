import logging

from fastapi import HTTPException, Request

from libs.auth_lib.utils import get_user_id_from_request
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.redis import RedisClient
from libs.utils_lib.core.security import get_client_ip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TIME_EQUIVALENT_IN_SECONDS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}


class Limiter:
    """
    A rate limiter class that uses Redis to limit the number of requests
    """

    redis_client: RedisClient
    enable_limiter: bool = True

    def __init__(self, rules: str) -> None:
        """
        Initialize the rate limiter with rules.

        Args:
            rules (str): A comma-separated string of rate limit rules in the format "count/unit".
                         Example: "10/second, 100/minute, 1000/hour".
        """
        self.rules = []
        # Use Lua script for atomic increment and expiry
        self.REDIS_LUA_INCREMENT = """
        local current = redis.call("INCR", KEYS[1])
        if tonumber(current) == 1 then
            redis.call("EXPIRE", KEYS[1], ARGV[1])
        end
        return current
        """
        for rule in rules.split(","):
            rule = rule.strip()
            if not rule:
                continue
            count, unit = rule.split("/")
            self.rules.append(
                (int(count), unit.strip(), TIME_EQUIVALENT_IN_SECONDS[unit.strip()])
            )

    async def __call__(self, request: Request) -> None:
        """
        Check if the request exceeds the rate limit.

        Args:
            request (Request): The incoming HTTP request.
        """
        if not self.enable_limiter:
            return None
        # Bypass rate limiter with header for local or staging environments
        if request.headers.get(
            "X-Bypass-RateLimit"
        ) and utils_lib_settings.ENVIRONMENT in ["local", "staging"]:
            logger.info("Bypassing rate limit for request.")
            return None

        try:
            redis = await self.redis_client.get_client()
        except Exception:
            logger.warning("Redis client is not initialized or connected.")
            return None

        identifier_base = await self.get_identifier(request)

        for count, unit, expiry in self.rules:
            key = f"{identifier_base}:{unit}"
            try:
                current_count = await redis.eval(
                    self.REDIS_LUA_INCREMENT, 1, key, expiry
                )

                if int(current_count) > count:
                    raise HTTPException(
                        status_code=429,
                        detail="Too Many Requests",
                        headers={"Retry-After": str(expiry)},
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Rate limit check failed for {key}: {e}")

        return None

    @classmethod
    def init(
        cls, redis_client: RedisClient, enable_limiter: bool | None = True
    ) -> None:
        """
        Initialize the Limiter class with a Redis client and enable/disable the limiter.

        Args:
            redis_client (RedisClient): An instance of RedisClient to connect to Redis.
            enable_limiter (bool, optional): Whether to enable the rate limiter. Defaults to True.
        """
        cls.redis_client = redis_client
        cls.enable_limiter = enable_limiter

    async def get_identifier(self, request: Request) -> str:
        """
        Generate a unique identifier for the request based on the client's IP address and request path.

        Args:
            request (Request): The incoming HTTP request.
        Returns:
            str: A unique identifier for the request.
        """
        # Try to get path from route
        route = request.scope.get("route")
        if not route or not getattr(route, "path", None):
            logger.error("Failed to resolve request path for rate limiting.")
            raise HTTPException(status_code=500, detail="Internal routing error.")
        # Prefer user ID from token if available
        user_id = await get_user_id_from_request(request)
        identity = str(user_id) if user_id else get_client_ip(request)
        return f"LIMITER:{identity}:{request.method}:{route.path}"
