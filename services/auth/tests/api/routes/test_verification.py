import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.utils import gen_email_verification_token
from libs.users_lib.models import Users
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)
from src.crud import create_user
from src.schemas import UserCreate


@pytest.mark.anyio
async def test_send_verification_email(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    await create_user(session=db, user_create=user_data)

    response = await client.get(f"/verification/email?email={email}")

    assert response.status_code == 200


@pytest.mark.anyio
async def test_verify_email(client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()

    create_response = await client.post(
        "/register",
        json={"username": username, "email": email, "password": test_password},
    )
    new_user = Users(**create_response.json())

    token = gen_email_verification_token(new_user.id)

    response = await client.get(f"/verification/email/{token}")

    assert response.status_code == 200


@pytest.mark.anyio
async def test_verify_email_invalid_token(client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()

    create_response = await client.post(
        "/register",
        json={"username": username, "email": email, "password": test_password},
    )
    new_user = Users(**create_response.json())

    token = f"{gen_email_verification_token(new_user.id)}invalid"

    response = await client.get(f"/verification/email/{token}")

    assert response.status_code == 401
