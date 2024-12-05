from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import session_manager
from app.core.security import (
    get_token_jti,
    is_access_token_blacklisted,
    security_settings,
)
from app.crud import get_user
from shared_lib.models import Users
from app.schemas import TokenData

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2 = OAuth2PasswordBearer(tokenUrl=f"http://auth.{settings.DOMAIN}/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get the database session from the session manager.

    Yields:
        AsyncSession: The database session.
    """
    if not session_manager.session_maker:
        raise Exception("Session manager not initialized")
    async with session_manager.session_maker() as session:
        yield session


async_session_dep = Annotated[AsyncSession, Depends(get_db)]
token_dep = Annotated[str, Depends(oauth2)]


async def get_user_from_token(session: async_session_dep, token: str) -> Users:
    """
    Get the user from the token.

    Args:
        session (AsyncSession): The database session.
        token (str): The token to decode.

    Returns:
        Users: The user object.
    """
    try:
        # Decode the token and get the user id
        payload = jwt.decode(
            token, settings.USERS_SECRET_KEY, algorithms=[security_settings.ALGORITHM]
        )
        user_id: UUID = payload.get("sub")

        if user_id is None:
            raise credential_exception

        token_data = TokenData(user_id=user_id)
    except (InvalidTokenError, ValidationError):
        raise credential_exception

    user = await get_user(session, user_id=token_data.user_id)

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
    access_jti = get_token_jti(token)
    if not access_jti or await is_access_token_blacklisted(access_jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessions does not exist"
        )

    return await get_user_from_token(session, token)


current_user = Annotated[Users, Depends(get_current_user)]
