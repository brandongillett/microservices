import time

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.models import Users
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.crud import get_outbox_event
from libs.utils_lib.models import ProcessedState
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)
from src.api.events import create_user_event


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
