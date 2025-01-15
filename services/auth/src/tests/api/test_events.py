import time

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.models import Users
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.crud import get_outbox_event
from libs.utils_lib.models import ProcessedState
from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
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

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.processed


@pytest.mark.anyio
async def test_verify_user_email_event(db: AsyncSession, client: AsyncClient) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    event = await verify_user_email_event(session=db, user_id=user.id)

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.processed
