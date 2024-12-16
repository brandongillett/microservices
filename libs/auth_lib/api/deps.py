from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

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
from src.api.deps import oauth2

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

token_dep = Annotated[str, Depends(oauth2)]


async def get_token_data(token: str) -> TokenData:
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
        user_role: str = payload.get("role")

        if not user_id:
            raise credential_exception

        token_data = TokenData(user_id=user_id, role=user_role)

        access_jti = get_token_jti(token)

        if await is_access_token_blacklisted(access_jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessions does not exist",
            )

        return token_data

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
    token_data = await get_token_data(token)

    user_id = token_data.user_id

    user = await get_user(session, user_id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user",
        )
    elif user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
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


async def get_current_user_token_data(token: token_dep) -> TokenData:
    """
    Get the current user ID from the token.

    Args:
        token (str): The token to decode.

    Returns:
        UUID: The user ID.
    """
    return await get_token_data(token)


current_user = Annotated[Users, Depends(get_current_user)]

# Dependency to get the token data (All services will use this dependency to retrieve the token data)
current_user_token_data = Annotated[UUID, Depends(get_current_user_token_data)]


class RoleChecker:
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, token_data: current_user_token_data) -> Any:
        if token_data.role in self.allowed_roles:
            return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
