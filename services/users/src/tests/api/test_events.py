import time
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.core.database import session_manager
from libs.utils_lib.crud import get_outbox_event
from libs.utils_lib.models import ProcessedState
from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
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

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.processed


@pytest.mark.anyio
async def test_update_user_username_event_invalid_user_id(db: AsyncSession) -> None:
    user_id = uuid4()
    new_username = random_lower_string()

    event = await update_user_username_event(
        session=db, user_id=user_id, new_username=new_username
    )

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.failed


@pytest.mark.anyio
async def test_update_user_password_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_password = "NewPassword@2"

    event = await update_user_password_event(
        session=db, user_id=user.id, new_password=new_password
    )

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.processed


@pytest.mark.anyio
async def test_update_user_password_event_invalid_user_id(db: AsyncSession) -> None:
    user_id = uuid4()
    new_password = "NewPassword@2"

    event = await update_user_password_event(
        session=db, user_id=user_id, new_password=new_password
    )

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.failed


@pytest.mark.anyio
async def test_update_user_role_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_role = "admin"

    event = await update_user_role_event(session=db, user_id=user.id, new_role=new_role)

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.processed


@pytest.mark.anyio
async def test_update_user_role_event_invalid_user_id(db: AsyncSession) -> None:
    user_id = uuid4()
    new_role = "admin"

    event = await update_user_role_event(session=db, user_id=user_id, new_role=new_role)

    time.sleep(0.2)  # Wait for the event to be processed

    # Create a new session to check the event status
    async with session_manager.get_session() as new_session:
        outbox_event = await get_outbox_event(session=new_session, event_id=event.id)

    assert outbox_event is not None

    assert outbox_event.processed == ProcessedState.failed
