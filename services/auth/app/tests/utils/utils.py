import random
import string
from datetime import datetime
from uuid import uuid4

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import create_refresh_token, create_user
from app.models import RefreshTokens
from shared_lib.models import Users
from app.schemas import RefreshTokenCreate
from shared_lib.schemas import UserCreate

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
    user_data = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=user_data)

    login_response = await client.post(
        "/auth/login",
        data={"username": username, "password": test_password},
    )
    tokens = login_response.json()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return headers, new_user


async def create_user_and_token(db: AsyncSession) -> tuple[Users, RefreshTokens]:
    """Helper function to create a user and a refresh token."""
    username = random_lower_string()
    email = random_email()
    user_create = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=user_create)

    time = datetime.utcnow()
    refresh_token_create = RefreshTokenCreate(
        user_id=new_user.id,
        refresh_jti=uuid4(),
        access_jti=uuid4(),
        created=time,
        expires=time,
        last_used=time,
        ip_address="0.0.0.0",
    )
    new_token = await create_refresh_token(
        session=db, refresh_token_create=refresh_token_create
    )

    return new_user, new_token
