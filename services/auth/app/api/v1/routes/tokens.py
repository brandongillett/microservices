from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.config import api_settings
from app.api.v1.deps import async_session_dep, current_user
from app.core.security import (
    blacklist_access_token,
)
from app.crud import (
    delete_refresh_token,
    get_refresh_token,
)
from app.schemas import (
    Message,
    RefreshTokensPublic,
)

router = APIRouter()


@router.get("", response_model=RefreshTokensPublic)
async def get_refresh_tokens(current_user: current_user) -> RefreshTokensPublic:
    """
    Get the current user refresh tokens.

    Returns:
        RefreshTokensPublic: The current user sessions.
    """
    tokens = current_user.refresh_tokens

    return RefreshTokensPublic(refresh_tokens=tokens, count=len(tokens))


@router.delete("/{token_id}", response_model=Message)
async def revoke_refresh_token(
    session: async_session_dep, current_user: current_user, token_id: UUID
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
