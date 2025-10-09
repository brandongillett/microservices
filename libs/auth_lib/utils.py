from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from libs.auth_lib.api.deps import get_token_data
from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.core.security import gen_url_token, verify_url_token


# Auth Token Extraction from Request
async def get_user_id_from_request(request: Request) -> UUID | None:
    """
    Attempts to extract the user ID from the Authorization header in the request.

    Args:
        request (Request): The incoming HTTP request.
    Returns:
        UUID | None: The user ID if extraction and validation are successful, otherwise None.
    """
    auth_header = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(auth_header)

    if not token or scheme.lower() != "bearer":
        return None

    try:
        token_data = await get_token_data(token, required_type="access")
        return token_data.user_id
    except (InvalidTokenError, ValidationError, HTTPException):
        return None


# Token Generation and Verification
def gen_email_verification_token(user_id: UUID) -> str:
    """
    Generate an email verification token with the provided data.

    Args:
        user_id (UUID): The user ID to encode in the token.

    Returns:
        str: The email verification token.
    """
    data = {"user_id": str(user_id)}
    return gen_url_token(data, "email_verification")


def verify_email_verification_token(token: str) -> UUID:
    """
    Verify an email verification token and extract the data.

    Args:
        token (str): The token to verify

    Returns:
        user_id (UUID): The user ID extracted from the token.
    """
    token_data = verify_url_token(
        token=token,
        salt="email_verification",
        expiration=auth_lib_security_settings.EMAIL_VERIFICATION_EXPIRES_MINUTES,
    )

    user_id = UUID(token_data.get("user_id"))

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    return user_id


async def gen_password_reset_token(user_id: UUID) -> str:
    """
    Generate a password reset token with the provided user ID.

    Args:
        user_id (UUID): The user ID to encode in the token.

    Returns:
        str: The password reset token.
    """
    token_id = uuid4()

    data = {"user_id": str(user_id), "token_id": str(token_id)}

    redis_key = f"password_reset_token:{token_id}"
    redis = redis_client.client

    await redis.set(
        redis_key,
        str(user_id),
        nx=True,
        ex=auth_lib_security_settings.PASSWORD_RESET_EXPIRES_MINUTES * 60,
    )

    return gen_url_token(data, "password_reset")


async def verify_password_reset_token(token: str) -> tuple[UUID, UUID]:
    """
    Verify a password reset token and extract the user ID.

    Args:
        token (str): The token to verify.

    Returns:
        UUID: The user ID extracted from the token.
    """
    token_data = verify_url_token(
        token=token,
        salt="password_reset",
        expiration=auth_lib_security_settings.PASSWORD_RESET_EXPIRES_MINUTES,
    )

    user_id = UUID(token_data.get("user_id"))
    token_id = UUID(token_data.get("token_id"))

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    redis_key = f"password_reset_token:{token_id}"
    redis = redis_client.client
    stored_user_id = await redis.get(redis_key)

    if not stored_user_id or stored_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    return user_id, token_id


async def invalidate_password_reset_token(token_id: UUID) -> None:
    """
    Invalidate a password reset token by deleting it from Redis.

    Args:
        token_id (UUID): The token ID to invalidate.
    """
    redis_key = f"password_reset_token:{token_id}"
    redis = redis_client.client
    await redis.delete(redis_key)
