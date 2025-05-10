from typing import Annotated, Any, Literal
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from libs.auth_lib.core.security import (
    security_settings as auth_lib_security_settings,
)
from libs.auth_lib.schemas import TokenData
from libs.users_lib.crud import get_user
from libs.users_lib.models import Users
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.core.config import settings
from src.api.config import api_settings

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2 = OAuth2PasswordBearer(tokenUrl=api_settings.TOKEN_URL)

token_dep = Annotated[str, Depends(oauth2)]


async def get_token_data(
    token: str, required_type: Literal["access", "refresh"]
) -> TokenData:
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
        user_id: UUID = payload.get("user_id")
        role: str = payload.get("role")
        verified: bool = payload.get("verified")
        type: str = payload.get("type")

        if not user_id:
            raise credential_exception

        if type != required_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        token_data = TokenData(user_id=user_id, role=role, verified=verified, type=type)

        return token_data

    except (InvalidTokenError, ValidationError):
        raise credential_exception


async def get_user_from_token(
    session: async_session_dep, token: str, required_type: Literal["access", "refresh"]
) -> Users:
    """
    Get the user from the token.

    Args:
        session (AsyncSession): The database session.
        token (str): The token to decode.

    Returns:
        Users: The user object.
    """
    token_data = await get_token_data(token=token, required_type=required_type)

    user_id = token_data.user_id

    user = await get_user(session=session, user_id=user_id)

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

    return await get_user_from_token(
        session=session, token=token, required_type="access"
    )


async def get_current_user_token_data(token: token_dep) -> TokenData:
    """
    Get the current user ID from the token.

    Args:
        token (str): The token to decode.

    Returns:
        UUID: The user ID.
    """
    return await get_token_data(token=token, required_type="access")


current_user = Annotated[Users, Depends(get_current_user)]

# Dependency to get the token data (All services will use this dependency to retrieve the token data)
current_user_token_data = Annotated[UUID, Depends(get_current_user_token_data)]


class RoleChecker:
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, token_data: current_user_token_data) -> Any:
        if settings.REQUIRE_USER_VERIFICATION and not token_data.verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not verified",
            )
        if token_data.role in self.allowed_roles:
            return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
