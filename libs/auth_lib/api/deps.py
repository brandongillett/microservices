from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from app.api.deps import oauth2
from libs.auth_lib.core.security import (
    get_token_jti,
    is_access_token_blacklisted,
)
from libs.auth_lib.core.security import (
    security_settings as auth_lib_security_settings,
)
from libs.auth_lib.crud import get_user
from libs.auth_lib.models import Users
from libs.auth_lib.schemas import TokenData
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.core.config import settings

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


token_dep = Annotated[str, Depends(oauth2)]


# Dependency to validate the token (All services will use this to return the user_id while checking if the token is valid)
async def validate_token(token: str) -> UUID:
    """
    Validates an access token and optionally checks if it's blacklisted.

    Args:
        token (str): The JWT access token.
        blacklist_check (callable, optional): Function to check if the token is blacklisted.

    Returns:
        UUID: The user ID extracted from the token.

    Raises:
        HTTPException: If the token is invalid, blacklisted, or malformed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[auth_lib_security_settings.ALGORITHM],
        )
        user_id: UUID = payload.get("sub")

        if not user_id:
            raise credential_exception

        token_data = TokenData(user_id=user_id)

        access_jti = get_token_jti(token)

        if await is_access_token_blacklisted(access_jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessions does not exist",
            )

        return token_data.user_id

    except (InvalidTokenError, ValidationError):
        raise credential_exception


async def get_user_from_token(session: async_session_dep, token: str) -> Users:
    """
    Get the user from the token.

    Args:
        session (AsyncSession): The database session.
        token (str): The token to decode.

    Returns:
        Users: The user object.
    """
    user_id = await validate_token(token)

    user = await get_user(session, user_id=user_id)

    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or non-existent user",
        )

    return user


async def get_current_user(session: async_session_dep, token: token_dep) -> Users:
    """
    Get the current user from the token.

    Args:
        session (AsyncSession): The database session.
        token (str): The token to decode.

    Returns:
        Users: The user object.
    """

    return await get_user_from_token(session, token)


current_user = Annotated[Users, Depends(get_current_user)]

# Dependency to get the current user ID (All services will use this dependency to get the user ID)
current_user_id = Annotated[UUID, Depends(validate_token)]
