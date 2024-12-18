from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from libs.auth_lib.api.deps import RoleChecker, current_user
from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.schemas import Message
from src.api.config import api_settings
from src.core.security import (
    blacklist_access_token,
)
from src.crud import (
    delete_refresh_token,
    get_refresh_token,
    get_refresh_tokens,
)
from src.schemas import (
    RefreshTokensPublic,
)

router = APIRouter()

all_roles = RoleChecker(allowed_roles=auth_lib_security_settings.roles)


@router.get(
    "",
    response_model=RefreshTokensPublic,
    dependencies=[Depends(all_roles)],
)
async def get_user_refresh_tokens(
    session: async_session_dep, current_user: current_user
) -> RefreshTokensPublic:
    """
    Get the current user refresh tokens.

    Returns:
        RefreshTokensPublic: The current user sessions.
    """
    tokens = await get_refresh_tokens(session=session, user_id=current_user.id)

    return RefreshTokensPublic(refresh_tokens=tokens, count=len(tokens))


@router.delete(
    "/{token_id}",
    response_model=Message,
    dependencies=[Depends(all_roles)],
)
async def revoke_user_refresh_token(
    session: async_session_dep,
    current_user: current_user,
    token_id: UUID,
) -> Message:
    """
    Revoke a user refresh token.

    Args:
        session (AsyncSession): The database session.
        current_user (User): The current user.
        token_id (UUID): The refresh token id.

    Returns:
        Message: The response message.
    """
    # Check if the refresh token exists
    refresh_token = await get_refresh_token(
        session=session, user_id=current_user.id, refresh_token_id=token_id
    )
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token not found")

    last_used = refresh_token.last_used
    current_time = datetime.utcnow()

    # Delete the refresh token from the database
    await delete_refresh_token(
        session=session, user_id=current_user.id, refresh_token_id=token_id
    )

    # Add Access JTI to redis blacklist if access token has not expired
    if (current_time - last_used) < timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    ):
        expiration_time = timedelta(
            minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ) - (current_time - last_used)
        await blacklist_access_token(refresh_token.access_jti, expiration_time)

    return Message(message="Refresh token deleted successfully")
