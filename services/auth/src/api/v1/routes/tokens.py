from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from libs.auth_lib.api.deps import gen_auth_token_dep
from libs.utils_lib.api.deps import async_read_session_dep, async_session_dep
from libs.utils_lib.core.limiter import Limiter
from libs.utils_lib.schemas import Message
from src.api.config import api_settings
from src.crud import (
    delete_refresh_token,
    get_refresh_token,
    get_refresh_tokens,
)
from src.schemas import (
    RefreshTokensPublic,
)

router = APIRouter()


@router.get(
    "/me",
    response_model=RefreshTokensPublic,
    dependencies=[Depends(Limiter("30/minute,300/hour"))],
)
async def get_user_refresh_tokens(
    session: async_read_session_dep, user_token: gen_auth_token_dep
) -> RefreshTokensPublic:
    """
    Get the current user refresh tokens.

    Args:
        session (AsyncSession): The database session.
        user_token (TokenData): The user's token data.

    Returns:
        RefreshTokensPublic: The current user sessions.
    """
    tokens = await get_refresh_tokens(session=session, user_id=user_token.user_id)

    return RefreshTokensPublic(refresh_tokens=tokens, count=len(tokens))


@router.delete(
    "/me/{token_id}",
    response_model=Message,
    dependencies=[
        Depends(Limiter(f"{api_settings.MAX_REFRESH_TOKENS}/minute,50/hour"))
    ],
)
async def revoke_user_refresh_token(
    session: async_session_dep,
    user_token: gen_auth_token_dep,
    token_id: UUID,
) -> Message:
    """
    Revoke a user refresh token.

    Args:
        session (AsyncSession): The database session.
        user_token (TokenData): The user's token data.
        token_id (UUID): The refresh token id.

    Returns:
        Message: The response message.
    """
    # Check if the refresh token exists
    refresh_token = await get_refresh_token(
        session=session, user_id=user_token.user_id, token_id=token_id
    )
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token not found")

    # Delete the refresh token from the database
    await delete_refresh_token(
        session=session, user_id=user_token.user_id, token_id=token_id
    )

    return Message(message="Refresh token deleted successfully")
