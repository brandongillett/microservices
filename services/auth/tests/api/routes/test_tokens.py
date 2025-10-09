from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.tests.utils.utils import create_and_login_user_helper
from src.crud import create_refresh_token
from src.schemas import RefreshTokenCreate


# User Sessions
@pytest.mark.anyio
async def test_get_refresh_tokens(db: AsyncSession, client: AsyncClient) -> None:
    headers, new_user = await create_and_login_user_helper(db, client)

    current_time = datetime.utcnow()

    token = await create_refresh_token(
        session=db,
        refresh_token_create=RefreshTokenCreate(
            user_id=new_user.id,
            jti=uuid4(),
            created_at=current_time,
            expires_at=current_time - timedelta(days=1),
            last_used_at=current_time,
            ip_address="0.0.0.0",
        ),
    )

    tokens_response = await client.get("/tokens/me", headers=headers)
    tokens = [
        refresh_token["id"]
        for refresh_token in tokens_response.json()["refresh_tokens"]
    ]

    assert tokens_response.status_code == 200
    assert str(token.id) in tokens


@pytest.mark.anyio
async def test_revoke_refresh_token(db: AsyncSession, client: AsyncClient) -> None:
    headers, new_user = await create_and_login_user_helper(db, client)

    current_time = datetime.utcnow()

    token = await create_refresh_token(
        session=db,
        refresh_token_create=RefreshTokenCreate(
            user_id=new_user.id,
            jti=uuid4(),
            created_at=current_time,
            expires_at=current_time - timedelta(days=1),
            last_used_at=current_time,
            ip_address="0.0.0.0",
        ),
    )

    tokens_response = await client.get("/tokens/me", headers=headers)
    tokens = [
        refresh_token["id"]
        for refresh_token in tokens_response.json()["refresh_tokens"]
    ]

    assert tokens_response.status_code == 200
    assert str(token.id) in tokens

    revoke_response = await client.delete(
        f"/tokens/me/{token.id}",
        headers=headers,
    )
    tokens_response = await client.get("/tokens/me", headers=headers)
    tokens = [
        refresh_token["id"]
        for refresh_token in tokens_response.json()["refresh_tokens"]
    ]

    assert revoke_response.status_code == 200
    assert str(token.id) not in tokens


@pytest.mark.anyio
async def test_revoke_refresh_token_invalid_token(
    db: AsyncSession, client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user_helper(db, client)

    revoke_response = await client.delete(
        f"/tokens/me/{uuid4()}",
        headers=headers,
    )

    assert revoke_response.status_code == 400
