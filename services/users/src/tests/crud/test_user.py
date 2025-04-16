import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.core.security import verify_password
from libs.users_lib.crud import (
    get_user,
    get_user_by_email,
    get_user_by_username,
    update_user_role,
    update_user_username,
)
from libs.users_lib.models import UserRole
from libs.utils_lib.tests.utils.utils import (
    random_lower_string,
)
from src.crud import update_user_password
from src.tests.utils.utils import create_random_user_helper


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
async def test_update_user_password(db: AsyncSession) -> None:
    new_user = await create_random_user_helper(db)

    new_password = "NewPassword@2"

    updated_user = await update_user_password(
        session=db, user_id=new_user.id, new_password=new_password
    )

    assert updated_user
    assert verify_password(new_password, updated_user.password)


@pytest.mark.anyio
async def test_update_user_role(db: AsyncSession) -> None:
    new_user = await create_random_user_helper(db)

    new_role = UserRole.admin

    updated_user = await update_user_role(
        session=db, user_id=new_user.id, role=new_role
    )

    assert updated_user
    assert updated_user.role == new_role
