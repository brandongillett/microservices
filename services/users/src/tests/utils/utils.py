from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from libs.auth_lib.core.security import get_password_hash
from libs.users_lib.models import Users
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)


async def create_random_user(db: AsyncSession) -> Users:
    """
    Create a random user.

    Args:
        db (AsyncSession): The database session.

    Returns:
        Users: The created user.
    """
    username = random_lower_string()
    email = random_email()

    new_user = Users(
        username=username, email=email, password=get_password_hash(test_password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def login_root_user(auth_client: AsyncClient) -> dict[str, str]:
    """
    Login the root user.

    Args:
        auth_client (AsyncClient): The auth client.

    Returns:
        str: The access token.
    """
    login_response = await auth_client.post(
        "/auth/login",
        data={"username": "root", "password": utils_lib_settings.ROOT_USER_PASSWORD},
    )
    login_json = login_response.json()
    token = login_json["access_token"]

    return {"Authorization": f"Bearer {token}"}
