import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.models import Users
from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
    event_processed_helper,
    random_email,
    random_lower_string,
    test_password,
)
from src.api.events import create_user_event, verify_user_email_event


@pytest.mark.anyio
async def test_create_user_event(db: AsyncSession) -> None:
    user = Users(
        username=random_lower_string(), email=random_email(), password=test_password
    )

    event = await create_user_event(session=db, user=user)

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_verify_user_email_event(db: AsyncSession, client: AsyncClient) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    event = await verify_user_email_event(session=db, user_id=user.id)

    processed = await event_processed_helper(event.id)

    assert processed
