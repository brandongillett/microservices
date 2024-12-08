from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings


# Security Settings
class security_settings(BaseSettings):
    # Rate limit settings
    def get_enable_rate_imit(self) -> bool:
        return settings.ENVIRONMENT != "local"

    # rate limiting disabled in local environment
    ENABLE_RATE_LIMIT = property(get_enable_rate_imit)


security_settings = security_settings()  # type: ignore

# Rate limit settings
rate_limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
if not security_settings.ENABLE_RATE_LIMIT:
    rate_limiter.enabled = False


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    _ = request  # Unused variable (mandatory for rate limiter)
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded (Please try again later)"},
        )
    # Handle other exceptions if necessary
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )
