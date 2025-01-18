from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.schemas import CreateUserEvent, VerifyUserEmailEvent
from libs.users_lib.models import Users
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
    event_processed_helper,
    random_email,
    random_lower_string,
    test_password,
)


@pytest.mark.anyio
async def test_create_user_event(db: AsyncSession) -> None:
    user = Users(
        username=random_lower_string(), email=random_email(), password=test_password
    )

    event_id = uuid4()
    event_schema = CreateUserEvent(event_id=event_id, user=user)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type="create_user",
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(session=db, event=event, event_schema=event_schema)

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_verify_user_email_event(db: AsyncSession, client: AsyncClient) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    event_id = uuid4()
    event_schema = VerifyUserEmailEvent(event_id=event_id, user_id=user.id)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type="verify_user_email",
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(session=db, event=event, event_schema=event_schema)

    processed = await event_processed_helper(event.id)

    assert processed
