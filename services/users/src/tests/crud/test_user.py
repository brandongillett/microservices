import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.core.security import verify_password
from libs.users_lib.crud import get_user
from libs.utils_lib.tests.utils.utils import (
    random_lower_string,
)
from src.crud import (
    update_user_password,
    update_user_username,
)
from src.tests.utils.utils import create_random_user


@pytest.mark.anyio
async def test_update_user_username(db: AsyncSession) -> None:
    new_user = await create_random_user(db)

    new_username = random_lower_string()

    await update_user_username(
        session=db, user_id=new_user.id, new_username=new_username
    )

    user = await get_user(session=db, user_id=new_user.id)
    assert user is not None, "User not found"

    assert user.username == new_username


@pytest.mark.anyio
async def test_update_user_password(db: AsyncSession) -> None:
    new_user = await create_random_user(db)

    new_password = "NewPassword@2"

    await update_user_password(
        session=db, user_id=new_user.id, new_password=new_password
    )

    user = await get_user(session=db, user_id=new_user.id)
    assert user is not None, "User not found"

    assert verify_password(new_password, user.password)
