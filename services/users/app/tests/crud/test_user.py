import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import verify_password
from app.crud import (
    create_user,
    update_user_password,
    update_user_username,
)
from shared_lib.schemas import UserCreate
from app.tests.utils.utils import random_email, random_lower_string, test_password


@pytest.mark.anyio
async def test_update_user_username(db: AsyncSession) -> None:
    username = random_lower_string()
    email = random_email()

    create = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=create)
    new_username = random_lower_string()

    await update_user_username(session=db, user=new_user, new_username=new_username)

    assert new_user.username == new_username


@pytest.mark.anyio
async def test_update_user_password(db: AsyncSession) -> None:
    username = random_lower_string()
    email = random_email()

    create = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=create)
    new_password = "NewPassword@2"
    await update_user_password(session=db, user=new_user, new_password=new_password)

    assert verify_password(new_password, new_user.password)
