import pytest
from httpx import AsyncClient
from shared_lib.models import Users
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import verify_password
from app.crud import (
    update_user_password,
    update_user_username,
)
from app.tests.utils.utils import random_email, random_lower_string, test_password


@pytest.mark.anyio
async def test_update_user_username(db: AsyncSession, auth_client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()

    create_response = await auth_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )
    new_user = Users(**create_response.json())

    new_username = random_lower_string()

    await update_user_username(session=db, user=new_user, new_username=new_username)

    assert new_user.username == new_username


@pytest.mark.anyio
async def test_update_user_password(db: AsyncSession, auth_client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()

    create_response = await auth_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )
    new_user = Users(**create_response.json())

    new_password = "NewPassword@2"
    await update_user_password(session=db, user=new_user, new_password=new_password)

    assert verify_password(new_password, new_user.password)
