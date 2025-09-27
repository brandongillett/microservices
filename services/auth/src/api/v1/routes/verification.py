from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from libs.auth_lib.api.events import (
    VERIFICATION_SEND_ROUTE,
    VERIFY_USER_ROUTE,
)
from libs.auth_lib.crud import verify_user_email
from libs.auth_lib.schemas import (
    VerificationSendEvent,
    VerifyUserEvent,
)
from libs.auth_lib.utils import (
    verify_email_verification_token,
)
from libs.users_lib.crud import get_user, get_user_by_email
from libs.utils_lib.api.deps import async_read_session_dep, async_session_dep
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.limiter import Limiter
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.schemas import Message

router = APIRouter()


@router.get(
    "/email",
    response_model=Message,
    dependencies=[Depends(Limiter("5/minute,15/hour,25/day"))],
)
async def send_verification_email(
    request: Request, session: async_read_session_dep, email: str
) -> Message:
    """
    Send verification email.

    Args:
        session (AsyncSession): The database session.
        email (str): The email address to send the verification email to.

    Returns:
        Message: The response message.
    """
    _ = request  # Unused variable (mandatory for rate limiter)

    user = await get_user_by_email(session=session, email=email)

    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive",
        )

    if user.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        )

    # Create email verification event
    event_emails_send_verification_id = uuid4()
    event_emails_send_verification_schema = VerificationSendEvent(
        event_id=event_emails_send_verification_id, user=user
    )

    event_emails_send_verification = await create_outbox_event(
        session=session,
        event_id=event_emails_send_verification_id,
        event_type=VERIFICATION_SEND_ROUTE.subject_for("emails"),
        data=event_emails_send_verification_schema.model_dump(mode="json"),
        commit=True,
    )

    # Publish the event
    await handle_publish_event(
        session=session,
        event=event_emails_send_verification,
        event_schema=event_emails_send_verification_schema,
    )

    return Message(message="Successfully sent verification email")


# Change back to post when frontend is ready
@router.get(
    "/email/{token}",
    response_model=Message,
    dependencies=[Depends(Limiter("20/minute"))],
)
async def verify_email(
    request: Request, session: async_session_dep, token: str
) -> Message:
    """
    Verify email address.

    Args:
        session (AsyncSession): The database session.
        token (str): The verification token.

    Returns:
        Message: The response message.
    """
    _ = request  # Unused variable (mandatory for rate limiter)

    user_id = verify_email_verification_token(token)

    # Check if user exists
    user = await get_user(session, user_id=user_id)

    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive",
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
    event_users_verify_user_id = uuid4()
    event_users_verify_user_schema = VerifyUserEvent(
        event_id=event_users_verify_user_id, user_id=user_id
    )

    event_users_verify_user = await create_outbox_event(
        session=session,
        event_id=event_users_verify_user_id,
        event_type=VERIFY_USER_ROUTE.subject_for("users"),
        data=event_users_verify_user_schema.model_dump(mode="json"),
        commit=False,
    )

    # Create verify user email event
    event_emails_verify_user_id = uuid4()
    event_emails_verify_user_schema = VerifyUserEvent(
        event_id=event_emails_verify_user_id, user_id=user_id
    )

    event_emails_verify_user = await create_outbox_event(
        session=session,
        event_id=event_emails_verify_user_id,
        event_type=VERIFY_USER_ROUTE.subject_for("emails"),
        data=event_emails_verify_user_schema.model_dump(mode="json"),
        commit=False,
    )

    # Commit and refresh the user
    await session.commit()
    await session.refresh(verified_user)
    await session.refresh(event_users_verify_user)
    await session.refresh(event_emails_verify_user)

    # Publish the events
    await handle_publish_event(
        session=session,
        event=event_users_verify_user,
        event_schema=event_users_verify_user_schema,
    )
    await handle_publish_event(
        session=session,
        event=event_emails_verify_user,
        event_schema=event_emails_verify_user_schema,
    )

    return Message(message="Successfully verified email")
