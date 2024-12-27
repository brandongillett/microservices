from datetime import datetime
from uuid import uuid4

from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.models import Users
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)
from src.crud import create_refresh_token, create_user
from src.models import RefreshTokens
from src.schemas import RefreshTokenCreate, UserCreate


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
        created_at=time,
        expires_at=time,
        last_used_at=time,
        ip_address="0.0.0.0",
    )
    new_token = await create_refresh_token(
        session=db, refresh_token_create=refresh_token_create
    )

    return new_user, new_token
