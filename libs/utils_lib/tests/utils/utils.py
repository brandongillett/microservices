import random
import string

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.models import Users

test_password = "Password@2"


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=20))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


async def create_and_login_user(
    db: AsyncSession, client: AsyncClient
) -> tuple[dict[str, str], Users]:
    """Helper function to create a user and login."""
    username = random_lower_string()
    email = random_email()

    create_response = await client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )
    new_user = Users(**create_response.json())

    await db.commit()

    login_response = await client.post(
        "/auth/login",
        data={"username": username, "password": test_password},
    )
    tokens = login_response.json()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return headers, new_user


async def create_and_login_user_auth_client(
    db: AsyncSession, auth_client: AsyncClient
) -> tuple[dict[str, str], Users]:
    """Helper function to create a user and login."""
    username = random_lower_string()
    email = random_email()

    create_response = await auth_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )

    new_user = Users(**create_response.json())

    await db.commit()

    login_response = await auth_client.post(
        "/auth/login",
        data={"username": username, "password": test_password},
    )
    tokens = login_response.json()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return headers, new_user
