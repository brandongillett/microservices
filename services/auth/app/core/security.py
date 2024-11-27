from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic_settings import BaseSettings
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.redis import redis_client


# Security Settings
class security_settings(BaseSettings):
    # Hashing algorithm (for tokens)
    ALGORITHM: str = "HS256"

    # Username and password constraints
    USERNAME_MIN_LENGTH: int = 5
    USERNAME_MAX_LENGTH: int = 22
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 40
    # Login lockout settings
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION: timedelta = timedelta(minutes=10)

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
        ex=security_settings.LOCKOUT_DURATION,
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


# JWT token blacklist
async def is_access_token_blacklisted(jti: UUID) -> bool:
    """
    Check if an access token is blacklisted.

    Args:
        jti (UUID): The JTI (unique identifier) of the access token

    Returns:
        bool: True if the token is blacklisted, False otherwise.
    """
    client = await redis_client.get_client()
    result = await client.get(f"{str(jti)}_blacklisted")
    return result is not None


async def blacklist_access_token(jti: UUID, expiration_time: timedelta) -> None:
    """
    Blacklist an access token by adding its JTI to the redis blacklist.

    Args:
        jti (UUID): The JTI (unique identifier) of the access token
        expiration_time (timedelta): The time until the token expires
    """
    client = await redis_client.get_client()
    await client.set(
        f"{str(jti)}_blacklisted",
        "true",
        ex=expiration_time,
    )


# JTI token extraction
def get_token_jti(token: str) -> UUID | None:
    """
    Extract the JTI (unique identifier) from a JWT token.

    Args:
        token (str): The JWT token to extract the JTI from

    Returns:
        UUID | None: The JTI of the token, or None if the token is invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.AUTH_SECRET_KEY, algorithms=[security_settings.ALGORITHM]
        )
        jti = payload.get("jti")
        return UUID(jti)
    except jwt.PyJWTError:
        return None


# JWT token generation
def gen_token(data: dict[str, Any], expire: datetime) -> tuple[str, UUID]:
    """
    Generate a JWT token with the provided data and expiration time.

    Args:
        data (dict[str, Any]): The data to encode in the token
        expire (datetime): The expiration time of the token

    Returns:
        tuple[str, UUID]: The encoded JWT token and its JTI (unique identifier)
    """
    jti = uuid4()

    to_encode = data.copy()

    to_encode.update({"exp": expire})
    to_encode.update({"jti": str(jti)})
    encoded_JWT = jwt.encode(
        to_encode, settings.AUTH_SECRET_KEY, algorithm=security_settings.ALGORITHM
    )
    return encoded_JWT, jti


# Client IP and location
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


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        plain_password (str): The plain text password to verify
        hashed_password (str): The hashed password to verify against

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get the hash of a password.

    Args:
        password (str): The password to hash

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


# Username and password validation
def is_username_complex(username: str) -> str | None:
    """
    Check if a username meets the required complexity.

    Username rules:
    - Must be between USERNAME_MIN_LENGTH and USERNAME_MAX_LENGTH characters long
    - Must not contain spaces
    - Must not start or end with underscores (_) or periods (.)
    - Must not contain consecutive underscores (_) or periods (.)
    - Must contain only alphanumeric characters, underscores, and periods

    Args:
        username (str): The username to validate

    Returns:
        str | None: An error message if the username is invalid, None otherwise.
    """

    # Check if username is between 5 and 22 characters long
    if not (
        security_settings.USERNAME_MIN_LENGTH
        <= len(username)
        <= security_settings.USERNAME_MAX_LENGTH
    ):
        return f"Username must be between {security_settings.USERNAME_MIN_LENGTH} and {security_settings.USERNAME_MAX_LENGTH} characters long"
    if username[0] in "_." or username[-1] in "_.":
        return "Username must not start or end with underscores (_) or periods (.)"

    # Check if username contains only alphanumeric characters, underscores, and periods, and no consecutive underscores or periods
    last_char = ""
    for char in username:
        if char.isspace():
            return "Username must not contain spaces"
        if not char.isalnum() and char not in "_.":
            return "Username contains an invalid character"
        if char == last_char and char in "_.":
            return (
                "Username must not contain consecutive underscores (_) or periods (.)"
            )
        last_char = char

    return None


def is_password_complex(password: str) -> str | None:
    """
    Check if a password meets the required complexity.

    Password rules:
    - Must be between PASSWORD_MIN_LENGTH and PASSWORD_MAX_LENGTH characters long
    - Must not contain spaces
    - Must contain at least one letter
    - Must contain at least one digit
    - Must contain at least one uppercase letter
    - Must contain at least one lowercase letter
    - Must contain at least one special character (!@#$%^&*()-_=+[]{}|;:,.<>?/)

    Args:
        password (str): The password to validate

    Returns:
       str | None: An error message if the password is invalid, None otherwise.
    """

    special_chars = set("!@#$%^&*()-_=+[]{}|;:,.<>?/")

    if not (
        security_settings.PASSWORD_MIN_LENGTH
        <= len(password)
        <= security_settings.PASSWORD_MAX_LENGTH
    ):
        return f"Password must be between {security_settings.PASSWORD_MIN_LENGTH} and {security_settings.PASSWORD_MAX_LENGTH} characters long"

    has_alpha = has_digit = has_upper = has_lower = has_special = False

    for char in password:
        if not char.isalnum() and char not in special_chars:
            return "Password contains an invalid character"
        if char.isspace():
            return "Password must not contain spaces"
        if char.isalpha():
            has_alpha = True
        if char.isdigit():
            has_digit = True
        if char.isupper():
            has_upper = True
        if char.islower():
            has_lower = True
        if char in special_chars:
            has_special = True

    if not has_alpha:
        return "Password must contain at least one letter"
    if not has_digit:
        return "Password must contain at least one digit"
    if not has_upper:
        return "Password must contain at least one uppercase letter"
    if not has_lower:
        return "Password must contain at least one lowercase letter"
    if not has_special:
        return "Password must contain at least one special character"

    return None
