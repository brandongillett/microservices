from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.api.events import (
    CREATE_USER_ROUTE,
    FORGOT_PASSWORD_SEND_ROUTE,
    VERIFICATION_SEND_ROUTE,
    VERIFY_USER_ROUTE,
)
from libs.auth_lib.schemas import (
    CreateUserEvent,
    ForgotPasswordSendEvent,
    VerificationSendEvent,
    VerifyUserEvent,
)
from libs.auth_lib.utils import gen_password_reset_token
from libs.users_lib.api.events import PASSWORD_UPDATED_ROUTE, UPDATE_PASSWORD_ROUTE
from libs.users_lib.models import Users
from libs.users_lib.schemas import UpdateUserPasswordEvent, UserPasswordUpdatedEvent
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
async def test_users_create_user_event(db: AsyncSession) -> None:
    user = Users(
        username=random_lower_string(), email=random_email(), password=test_password
    )

    event_id = uuid4()
    event_schema = CreateUserEvent(event_id=event_id, user=user)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=CREATE_USER_ROUTE.subject_for("users"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(session=db, event=event, event_schema=event_schema)

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_emails_create_user_event(db: AsyncSession) -> None:
    user = Users(
        username=random_lower_string(), email=random_email(), password=test_password
    )

    event_id = uuid4()
    event_schema = CreateUserEvent(event_id=event_id, user=user)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=CREATE_USER_ROUTE.subject_for("emails"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(session=db, event=event, event_schema=event_schema)

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_emails_forgot_password_send_event(
    db: AsyncSession, client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    # Generate password reset token
    reset_token = await gen_password_reset_token(user_id=user.id)

    # Create forgot password event
    event_id = uuid4()
    event_schema = ForgotPasswordSendEvent(
        event_id=event_id, user_id=user.id, token=reset_token
    )

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=FORGOT_PASSWORD_SEND_ROUTE.subject_for("emails"),
        data=event_schema.model_dump(mode="json"),
    )

    # Publish the event
    await handle_publish_event(
        session=db,
        event=event,
        event_schema=event_schema,
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_users_update_password_event(
    db: AsyncSession, client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    new_password = "NewPassword@2"

    event_id = uuid4()
    event_schema = UpdateUserPasswordEvent(
        event_id=event_id, user_id=user.id, new_password=new_password
    )

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=UPDATE_PASSWORD_ROUTE.subject_for("users"),
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
    db: AsyncSession, client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

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
async def test_emails_verification_send_event(
    db: AsyncSession, client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    # Create email verification event
    event_id = uuid4()
    event_schema = VerificationSendEvent(event_id=event_id, user=user)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=VERIFICATION_SEND_ROUTE.subject_for("emails"),
        data=event_schema.model_dump(mode="json"),
        commit=True,
    )

    # Publish the event
    await handle_publish_event(
        session=db,
        event=event,
        event_schema=event_schema,
    )

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_users_verify_user_event(db: AsyncSession, client: AsyncClient) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    event_id = uuid4()
    event_schema = VerifyUserEvent(event_id=event_id, user_id=user.id)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=VERIFY_USER_ROUTE.subject_for("users"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(session=db, event=event, event_schema=event_schema)

    processed = await event_processed_helper(event.id)

    assert processed


@pytest.mark.anyio
async def test_emails_verify_user_email_event(
    db: AsyncSession, client: AsyncClient
) -> None:
    _, user = await create_and_login_user_helper(db=db, client=client)

    event_id = uuid4()
    event_schema = VerifyUserEvent(event_id=event_id, user_id=user.id)

    event = await create_outbox_event(
        session=db,
        event_id=event_id,
        event_type=VERIFY_USER_ROUTE.subject_for("emails"),
        data=event_schema.model_dump(mode="json"),
    )

    await handle_publish_event(session=db, event=event, event_schema=event_schema)

    processed = await event_processed_helper(event.id)

    assert processed
