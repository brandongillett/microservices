from datetime import datetime, timedelta
from uuid import UUID, uuid4

import jwt
from fastapi import Request
from pydantic_settings import BaseSettings

from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.auth_lib.schemas import TokenData
from libs.utils_lib.core.config import settings
from libs.utils_lib.core.redis import redis_client


# Security Settings
class security_settings(BaseSettings):
    # Login lockout settings
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15


security_settings = security_settings()  # type: ignore


# Login attempts (with redis)
async def increment_login_attempts(username: str) -> int:
    """
    Increment the login attempts for a user.

    Args:
        username (str): The username to increment the login attempts for

    Returns:
        int: The current number of login attempts for the user.
    """
    client = await redis_client.get_client()

    attempts = await client.get(f"{username}_login_attempts")
    current_attempts = int(attempts) + 1 if attempts else 1
    await client.set(
        f"{username}_login_attempts",
        current_attempts,
        ex=timedelta(minutes=security_settings.LOCKOUT_DURATION_MINUTES).seconds,
    )
    return current_attempts


async def get_login_attempts(username: str) -> int:
    """
    Get the number of login attempts for a user.

    Args:
        username (str): The username to get the login attempts for

    Returns:
        int: The current number of login attempts for the user.
    """
    client = await redis_client.get_client()
    attempts = await client.get(f"{username}_login_attempts")
    return int(attempts) if attempts else 0


async def reset_login_attempts(username: str) -> None:
    """
    Reset the login attempts for a user.

    Args:
        username (str): The username to reset the login attempts for
    """
    client = await redis_client.get_client()
    await client.delete(f"{username}_login_attempts")


# JWT token generation
def gen_token(data: TokenData, expire: datetime) -> tuple[str, UUID]:
    """
    Generate a JWT token with the provided data and expiration time.

    Args:
        data (TokenData): The data to encode in the token
        expire (datetime): The expiration time of the token

    Returns:
        tuple[str, UUID]: The encoded JWT token and its JTI (unique identifier)
    """
    jti = uuid4()

    to_encode = data.dict()
    to_encode["user_id"] = str(data.user_id)

    to_encode["exp"] = expire
    to_encode["jti"] = str(jti)

    encoded_JWT = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=auth_lib_security_settings.ALGORITHM
    )
    return encoded_JWT, jti


# Client IP
def get_client_ip(request: Request) -> str:
    """
    Get the client's IP address from the request.

    Args:
        request (Request): The request object

    Returns:
        str: The client's IP address
    """
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()  # Strip any whitespace
    else:
        if request.client is not None:  # Ensure request.client is not None
            ip = request.client.host
        else:
            ip = "0.0.0.0"  # Fallback IP address if client is None

    return ip  # Return the correct variable
