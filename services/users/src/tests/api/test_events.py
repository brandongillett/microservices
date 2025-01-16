import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
    event_processed_helper,
    random_lower_string,
)
from src.api.events import (
    update_user_password_event,
    update_user_role_event,
    update_user_username_event,
)


@pytest.mark.anyio
async def test_update_user_username_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_username = random_lower_string()

    event = await update_user_username_event(
        session=db, user_id=user.id, new_username=new_username
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_update_user_password_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_password = "NewPassword@2"

    event = await update_user_password_event(
        session=db, user_id=user.id, new_password=new_password
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_update_user_role_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_role = "admin"

    event = await update_user_role_event(session=db, user_id=user.id, new_role=new_role)

    processed = await event_processed_helper(event.id)

    assert processed
