from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.config import api_settings
from src.crud import (
    authenticate_refresh_token,
    create_refresh_token,
    delete_expired_tokens,
    delete_max_tokens,
    delete_refresh_token,
    get_refresh_token,
    get_refresh_tokens,
)
from src.schemas import RefreshTokenCreate
from src.tests.utils.utils import create_user_and_token


@pytest.mark.anyio
async def test_create_refresh_token(db: AsyncSession) -> None:
    new_user, new_token = await create_user_and_token(db)

    assert new_token
    assert new_token.id
    assert new_token.user_id == new_user.id
    assert new_token.refresh_jti
    assert new_token.access_jti
    assert new_token.created_at
    assert new_token.expires_at
    assert new_token.last_used_at
    assert new_token.ip_address


@pytest.mark.anyio
async def test_authenticate_refresh_token(db: AsyncSession) -> None:
    new_user, new_token = await create_user_and_token(db)

    authenticated_token = await authenticate_refresh_token(
        session=db, user_id=new_user.id, refresh_jti=new_token.refresh_jti
    )

    assert authenticated_token
    assert authenticated_token == new_token


@pytest.mark.anyio
async def test_delete_refresh_token(db: AsyncSession) -> None:
    new_user, new_token = await create_user_and_token(db)

    await delete_refresh_token(
        session=db, user_id=new_user.id, refresh_token_id=new_token.id
    )

    deleted_token = await authenticate_refresh_token(
        session=db, user_id=new_user.id, refresh_jti=new_token.refresh_jti
    )

    assert not deleted_token


@pytest.mark.anyio
async def test_get_refresh_token(db: AsyncSession) -> None:
    new_user, new_token = await create_user_and_token(db)

    token = await get_refresh_token(
        session=db, user_id=new_user.id, refresh_token_id=new_token.id
    )

    assert token
    assert token == new_token


@pytest.mark.anyio
async def test_get_refresh_tokens(db: AsyncSession) -> None:
    new_user, token = await create_user_and_token(db)

    tokens = await get_refresh_tokens(session=db, user_id=new_user.id)

    assert tokens
    assert len(tokens) == 1
    assert token in tokens


@pytest.mark.anyio
async def test_delete_expired_tokens(db: AsyncSession) -> None:
    new_user, _ = await create_user_and_token(db)

    current_time = datetime.utcnow()

    expired_token = await create_refresh_token(
        session=db,
        refresh_token_create=RefreshTokenCreate(
            user_id=new_user.id,
            refresh_jti=uuid4(),
            access_jti=uuid4(),
            created_at=current_time,
            expires_at=current_time - timedelta(days=1),
            last_used_at=current_time,
            ip_address="0.0.0.0",
        ),
    )
    not_expired_token = await create_refresh_token(
        session=db,
        refresh_token_create=RefreshTokenCreate(
            user_id=new_user.id,
            refresh_jti=uuid4(),
            access_jti=uuid4(),
            created_at=current_time,
            expires_at=current_time + timedelta(days=1),
            last_used_at=current_time,
            ip_address="0.0.0.0",
        ),
    )

    user_id = new_user.id

    tokens = await get_refresh_tokens(session=db, user_id=user_id)

    assert expired_token in tokens
    assert not_expired_token in tokens

    await delete_expired_tokens(session=db, user_id=user_id)
    tokens = await get_refresh_tokens(session=db, user_id=user_id)

    assert expired_token not in tokens
    assert not_expired_token in tokens


@pytest.mark.anyio
async def test_delete_max_tokens(db: AsyncSession) -> None:
    new_user, _ = await create_user_and_token(db)

    current_time = datetime.utcnow()

    for _ in range(api_settings.MAX_REFRESH_TOKENS):
        random_jti = uuid4()
        await create_refresh_token(
            session=db,
            refresh_token_create=RefreshTokenCreate(
                user_id=new_user.id,
                refresh_jti=random_jti,
                access_jti=random_jti,
                created_at=current_time,
                expires_at=current_time + timedelta(days=1),
                last_used_at=current_time,
                ip_address="",
            ),
        )

    tokens = await get_refresh_tokens(session=db, user_id=new_user.id)

    assert tokens
    assert len(tokens) == api_settings.MAX_REFRESH_TOKENS + 1

    await delete_max_tokens(session=db, user_id=new_user.id)
    tokens = await get_refresh_tokens(session=db, user_id=new_user.id)

    assert tokens
    assert len(tokens) == api_settings.MAX_REFRESH_TOKENS
