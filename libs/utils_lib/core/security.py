from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from itsdangerous import URLSafeTimedSerializer
from pydantic_settings import BaseSettings
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from libs.utils_lib.core.config import settings


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


# URL safe token generation and verification
def gen_url_token(data: dict, salt: str) -> str:
    """
    Generate a URL-safe token with the provided data and salt.

    Args:
        data (dict): The data to encode in the token
        salt (str): The salt to use for encoding

    Returns:
        str: The URL-safe token.
    """
    serializer = URLSafeTimedSerializer(secret_key=settings.SECRET_KEY, salt=salt)

    return serializer.dumps(data)


def verify_url_token(token: str, salt: str, expiration: int) -> dict:
    """
    Verify a URL-safe token and extract the data.

    Args:
        token (str): The token to verify
        salt (str): The salt to use for verification
        expiration (int): The maximum age of the token in minutes

    Returns:
        dict: The data extracted from the token. If the token is invalid or expired, an HTTPException is raised.
    """
    serializer = URLSafeTimedSerializer(secret_key=settings.SECRET_KEY, salt=salt)

    try:
        data = serializer.loads(token, max_age=expiration * 60)
        return data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
