from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status

from libs.auth_lib.api.deps import (
    credential_exception,
    get_token_data,
)
from libs.auth_lib.core.security import get_token_jti
from libs.utils_lib.api.deps import async_session_dep
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
        session=session, user_id=token_data.user_id, refresh_token_id=token_obj.id
    )

    response.delete_cookie("refresh_token")

    return token_obj


consumed_refresh_token = Annotated[RefreshTokens, Depends(consume_refresh_token)]
