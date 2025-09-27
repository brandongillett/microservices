from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.api.events import (
    PASSWORD_UPDATED_ROUTE,
    UPDATE_PASSWORD_ROUTE,
    UPDATE_ROLE_ROUTE,
    UPDATE_USERNAME_ROUTE,
)
from libs.users_lib.models import UserRole
from libs.users_lib.schemas import (
    UpdateUserPasswordEvent,
    UpdateUserRoleEvent,
    UpdateUserUsernameEvent,
    UserPasswordUpdatedEvent,
)
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
    event_processed_helper,
    random_lower_string,
)


@pytest.mark.anyio
async def test_auth_update_username_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_username = random_lower_string()

    event_id = uuid4()
    event_schema = UpdateUserUsernameEvent(
        event_id=event_id, user_id=user.id, new_username=new_username
    )

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=UPDATE_USERNAME_ROUTE.subject_for("auth"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(
        session=db,
        event=event,
        event_schema=event_schema,
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_emails_update_username_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_username = random_lower_string()

    event_id = uuid4()
    event_schema = UpdateUserUsernameEvent(
        event_id=event_id, user_id=user.id, new_username=new_username
    )

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=UPDATE_USERNAME_ROUTE.subject_for("emails"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(
        session=db,
        event=event,
        event_schema=event_schema,
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_auth_update_password_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_password = "NewPassword@2"

    event_id = uuid4()
    event_schema = UpdateUserPasswordEvent(
        event_id=event_id, user_id=user.id, new_password=new_password
    )

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=UPDATE_PASSWORD_ROUTE.subject_for("auth"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(
        session=db,
        event=event,
        event_schema=event_schema,
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_emails_password_updated_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    event_id = uuid4()
    event_schema = UserPasswordUpdatedEvent(event_id=event_id, user=user)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=PASSWORD_UPDATED_ROUTE.subject_for("emails"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(
        session=db,
        event=event,
        event_schema=event_schema,
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_auth_update_role_event(
    db: AsyncSession, auth_client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db, auth_client)

    new_role = UserRole.admin

    event_id = uuid4()
    event_schema = UpdateUserRoleEvent(
        event_id=event_id, user_id=user.id, new_role=new_role
    )

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=UPDATE_ROLE_ROUTE.subject_for("auth"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(
        session=db,
        event=event,
        event_schema=event_schema,
    )

    processed = await event_processed_helper(event.id)

    assert processed
