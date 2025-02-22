from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from libs.auth_lib.crud import verify_user_email
from libs.auth_lib.schemas import (
    VerifyUserEvent,
)
from libs.auth_lib.utils import verify_email_verification_token
from libs.users_lib.crud import get_user
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.schemas import Message

router = APIRouter()


# Change back to post when frontend is ready
@router.get("/email/{token}", response_model=Message)
async def verify_email(session: async_session_dep, token: str) -> Message:
    """
    Verify email address.

    Args:
        session (AsyncSession): The database session.
        token (str): The verification token.

    Returns:
        dict: The verification message.
    """
    user_id = verify_email_verification_token(token)

    # Check if user exists
    user = await get_user(session, user_id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        )

    # Verify email
    verified_user = await verify_user_email(
        session=session, user_id=user_id, commit=False
    )

    # Create verify user event
    verify_user_event_id = uuid4()
    verify_user_event_schema = VerifyUserEvent(
        event_id=verify_user_event_id, user_id=user_id
    )

    verify_user_event = await create_outbox_event(
        session=session,
        event_id=verify_user_event_id,
        event_type="users_service_verify_user",
        data=verify_user_event_schema.model_dump(mode="json"),
        commit=False,
    )

    # Create verify user email event
    verify_user_email_event_id = uuid4()
    verify_user_email_event_schema = VerifyUserEvent(
        event_id=verify_user_email_event_id, user_id=user_id
    )

    verify_user_email_event = await create_outbox_event(
        session=session,
        event_id=verify_user_email_event_id,
        event_type="emails_service_verify_user",
        data=verify_user_email_event_schema.model_dump(mode="json"),
        commit=False,
    )

    # Commit and refresh the user
    await session.commit()
    await session.refresh(verified_user)
    await session.refresh(verify_user_event)
    await session.refresh(verify_user_email_event)

    # Publish the events
    await handle_publish_event(
        session=session, event=verify_user_event, event_schema=verify_user_event_schema
    )
    await handle_publish_event(
        session=session,
        event=verify_user_email_event,
        event_schema=verify_user_email_event_schema,
    )

    return Message(message="Successfully verified email")
