from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from libs.auth_lib.api.deps import gen_auth_token_dep
from libs.auth_lib.core.security import (
    is_password_complex,
    is_username_valid,
    verify_password,
)
from libs.users_lib.api.events import (
    PASSWORD_UPDATED_ROUTE,
    UPDATE_PASSWORD_ROUTE,
    UPDATE_USERNAME_ROUTE,
)
from libs.users_lib.crud import (
    get_user,
    get_user_by_username,
    update_user_password,
    update_user_username,
)
from libs.users_lib.models import Users
from libs.users_lib.schemas import (
    UpdateUserPasswordEvent,
    UpdateUserUsernameEvent,
    UserPasswordUpdatedEvent,
    UserPublic,
)
from libs.utils_lib.api.deps import async_read_session_dep, async_session_dep
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.limiter import Limiter
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.schemas import Message
from src.schemas import (
    UpdatePassword,
    UpdateUsername,
)

router = APIRouter()


@router.get(
    "/me",
    response_model=UserPublic,
    dependencies=[Depends(Limiter("30/minute,300/hour"))],
)
async def my_details(
    session: async_read_session_dep, user_token: gen_auth_token_dep
) -> Users:
    """
    Get the current user details.

    Args:
        session (AsyncSession): The database session.
        user_token (TokenData): The user's token data.

    Returns:
        UserPublic: The current user details.
    """
    user = await get_user(session=session, user_id=user_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user",
        )

    return user


@router.patch(
    "/me/username",
    response_model=Message,
    dependencies=[Depends(Limiter("5/minute,15/hour,30/day"))],
)
async def update_username(
    session: async_session_dep, body: UpdateUsername, user_token: gen_auth_token_dep
) -> Message:
    """
    Update the current user username.

    Args:
        session (AsyncSession): The database session.
        body (UpdateUsername): The request body.
        user_token (TokenData): The user's token data.

    Returns:
        Message: The response message.
    """
    user = await get_user(session=session, user_id=user_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user",
        )

    # Check if the new username is the same as the current username
    if user.username == body.new_username:
        raise HTTPException(
            status_code=400,
            detail="New username cannot be the same as the current username",
        )

    # Check if the new username meets the required complexity
    username_complexity = is_username_valid(body.new_username)
    if username_complexity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=username_complexity
        )

    # Check if the new username is unique
    if await get_user_by_username(session=session, username=body.new_username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username is already taken"
        )

    # Convert the new username to lowercase
    body.new_username = body.new_username.lower()

    # Update the user username
    user = await update_user_username(
        session=session,
        user_id=user.id,
        new_username=body.new_username,
        commit=False,
    )

    # Auth event for updating username
    event_auth_update_username_id = uuid4()
    event_auth_update_username_schema = UpdateUserUsernameEvent(
        event_id=event_auth_update_username_id,
        user_id=user.id,
        new_username=body.new_username,
    )

    event_auth_update_username = await create_outbox_event(
        session=session,
        event_id=event_auth_update_username_id,
        event_type=UPDATE_USERNAME_ROUTE.subject_for("auth"),
        data=event_auth_update_username_schema.model_dump(mode="json"),
        commit=False,
    )

    # Emails event updating username
    event_emails_update_username_id = uuid4()
    event_emails_update_username_schema = UpdateUserUsernameEvent(
        event_id=event_emails_update_username_id,
        user_id=user.id,
        new_username=body.new_username,
    )

    event_emails_update_username = await create_outbox_event(
        session=session,
        event_id=event_emails_update_username_id,
        event_type=UPDATE_USERNAME_ROUTE.subject_for("emails"),
        data=event_emails_update_username_schema.model_dump(mode="json"),
        commit=False,
    )

    await session.commit()
    await session.refresh(user)
    await session.refresh(event_auth_update_username)
    await session.refresh(event_emails_update_username)

    # Publish events
    await handle_publish_event(
        session=session,
        event=event_auth_update_username,
        event_schema=event_auth_update_username_schema,
    )
    await handle_publish_event(
        session=session,
        event=event_emails_update_username,
        event_schema=event_emails_update_username_schema,
    )

    return Message(message=f"Username updated to {body.new_username}")


@router.patch(
    "/me/password",
    response_model=Message,
    dependencies=[Depends(Limiter("5/minute,15/hour,30/day"))],
)
async def update_password(
    session: async_session_dep, body: UpdatePassword, user_token: gen_auth_token_dep
) -> Message:
    """
    Update the current user password.

    Args:
        session (AsyncSession): The database session.
        body (UpdatePassword): The request body.
        user_token (TokenData): The user's token data.

    Returns:
        Message: The response message.
    """
    user = await get_user(session=session, user_id=user_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user",
        )

    # Check if the current password is correct
    if not await verify_password(body.current_password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    # Check if the new password is the same as the current password
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the current password",
        )

    # Check if the new password meets the required complexity
    password_complexity = is_password_complex(body.new_password)
    if password_complexity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=password_complexity
        )

    # Update the user password
    user = await update_user_password(
        session=session,
        user_id=user.id,
        new_password=body.new_password,
        commit=False,
    )

    # Auth event for updating password
    event_auth_update_password_id = uuid4()
    event_auth_update_password_schema = UpdateUserPasswordEvent(
        event_id=event_auth_update_password_id,
        user_id=user.id,
        new_password=user.password,
    )

    event_auth_update_password = await create_outbox_event(
        session=session,
        event_id=event_auth_update_password_id,
        event_type=UPDATE_PASSWORD_ROUTE.subject_for("auth"),
        data=event_auth_update_password_schema.model_dump(mode="json"),
        commit=False,
    )

    # Emails event for notifying password updated
    event_emails_password_updated_id = uuid4()
    event_emails_password_updated_schema = UserPasswordUpdatedEvent(
        event_id=event_emails_password_updated_id, user=user
    )

    event_emails_password_updated = await create_outbox_event(
        session=session,
        event_id=event_emails_password_updated_id,
        event_type=PASSWORD_UPDATED_ROUTE.subject_for("emails"),
        data=event_emails_password_updated_schema.model_dump(mode="json"),
        commit=False,
    )

    await session.commit()
    await session.refresh(user)
    await session.refresh(event_auth_update_password)
    await session.refresh(event_emails_password_updated)

    # Publish events
    await handle_publish_event(
        session=session,
        event=event_auth_update_password,
        event_schema=event_auth_update_password_schema,
    )

    await handle_publish_event(
        session=session,
        event=event_emails_password_updated,
        event_schema=event_emails_password_updated_schema,
    )

    return Message(message="Password updated successfully")
