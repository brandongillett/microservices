from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import (
    update_user_password,
    update_user_username,
)
from libs.auth_lib.models import Users
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)


@pytest.mark.anyio
async def test_update_user_username(db: AsyncSession, auth_client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()

    create_response = await auth_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )
    create_response_data = create_response.json()
    create_response_data["id"] = UUID(create_response_data["id"])
    new_user = Users(**create_response_data)
    await db.commit()

    new_username = random_lower_string()

    await update_user_username(
        session=db, user_id=new_user.id, new_username=new_username
    )

    login_response = await auth_client.post(
        "/auth/login",
        data={"username": new_username, "password": test_password},
    )

    assert login_response.status_code == 200


@pytest.mark.anyio
async def test_update_user_password(db: AsyncSession, auth_client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()

    create_response = await auth_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )
    create_response_data = create_response.json()
    create_response_data["id"] = UUID(create_response_data["id"])
    new_user = Users(**create_response_data)

    await db.commit()

    new_password = "NewPassword@2"

    await update_user_password(
        session=db, user_id=new_user.id, new_password=new_password
    )

    login_response = await auth_client.post(
        "/auth/login",
        data={"username": username, "password": new_password},
    )

    assert login_response.status_code == 200
