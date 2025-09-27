from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status

from libs.auth_lib.api.deps import (
    credential_exception,
    get_token_data,
)
from libs.auth_lib.core.security import get_token_jti
from libs.users_lib.crud import get_user, get_user_by_email, get_user_by_username
from libs.users_lib.models import Users
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.core.config import settings as utils_lib_settings
from src.crud import authenticate_refresh_token, delete_refresh_token
from src.models import RefreshTokens

app = FastAPI()


async def consume_refresh_token(
    session: async_session_dep, response: Response, request: Request
) -> RefreshTokens:
    token = request.cookies.get("refresh_token")
    if not token:
        raise credential_exception

    token_data = await get_token_data(token=token, required_type="refresh")

    jti = get_token_jti(token)
    if not jti:
        raise credential_exception

    token_obj = await authenticate_refresh_token(
        session=session, user_id=token_data.user_id, jti=jti
    )
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session no longer exists"
        )

    await delete_refresh_token(
        session=session, user_id=token_data.user_id, token_id=token_obj.id
    )

    response.delete_cookie("refresh_token")

    return token_obj


consumed_refresh_token = Annotated[RefreshTokens, Depends(consume_refresh_token)]


async def get_valid_user(
    session: async_session_dep,
    user_id: UUID | None = None,
    email: str | None = None,
    username: str | None = None,
) -> Users:
    """
    Confirms user exists and is valid before returning user object.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID to retrieve.

    Returns:
        Users: The user object if found and valid, otherwise raises HTTPException.
    """
    if not user_id and not email and not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_id, email, or username must be provided",
        )

    if user_id:
        user = await get_user(session=session, user_id=user_id)
    elif email:
        user = await get_user_by_email(session=session, email=email)
    elif username:
        user = await get_user_by_username(session=session, username=username)

    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive",
        )

    if utils_lib_settings.REQUIRE_USER_VERIFICATION and not user.verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not verified",
        )

    return user
