import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.tests.utils.utils import (
    random_lower_string,
)
from src.crud import (
    get_user,
    get_user_by_email,
    get_user_by_username,
    update_user_username,
    verify_user_email,
)
from tests.utils.utils import create_random_user_helper


@pytest.mark.anyio
async def test_get_user(db: AsyncSession) -> None:
    new_user = await create_random_user_helper(db)

    user = await get_user(session=db, user_id=new_user.id)

    assert user
    assert new_user == user


@pytest.mark.anyio
async def test_get_user_by_username(db: AsyncSession) -> None:
    new_user = await create_random_user_helper(db)

    user = await get_user_by_username(session=db, username=new_user.username)

    assert user
    assert new_user == user


@pytest.mark.anyio
async def test_get_user_by_email(db: AsyncSession) -> None:
    new_user = await create_random_user_helper(db)

    user = await get_user_by_email(session=db, email=new_user.email)

    assert user
    assert new_user == user


@pytest.mark.anyio
async def test_update_user_username(db: AsyncSession) -> None:
    new_user = await create_random_user_helper(db)

    new_username = random_lower_string()

    updated_user = await update_user_username(
        session=db, user_id=new_user.id, new_username=new_username
    )

    assert updated_user
    assert updated_user.username == new_username


@pytest.mark.anyio
async def test_verify_user_email(db: AsyncSession) -> None:
    new_user = await create_random_user_helper(db)

    verified_user = await verify_user_email(session=db, user_id=new_user.id)

    assert verified_user
    assert verified_user.verified
