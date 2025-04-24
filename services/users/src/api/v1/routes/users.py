from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from libs.auth_lib.api.deps import current_user
from libs.auth_lib.core.security import (
    is_password_complex,
    is_username_complex,
    verify_password,
)
from libs.auth_lib.utils import GEN_ROLE_CHECKER
from libs.users_lib.crud import get_user_by_username, update_user_username
from libs.users_lib.models import Users
from libs.users_lib.schemas import (
    UpdateUserPasswordEvent,
    UpdateUserUsernameEvent,
    UserPublic,
)
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.schemas import Message
from src.crud import update_user_password
from src.schemas import (
    UpdatePassword,
    UpdateUsername,
)

router = APIRouter()


@router.get("/me", response_model=UserPublic, dependencies=[Depends(GEN_ROLE_CHECKER)])
def my_details(current_user: current_user) -> Users:
    """
    Get the current user details.

    Returns:
        UserPublic: The current user details.
    """
    return current_user


@router.patch(
    "/me/username",
    response_model=Message,
    dependencies=[Depends(GEN_ROLE_CHECKER)],
)
async def update_username(
    session: async_session_dep, body: UpdateUsername, current_user: current_user
) -> Message:
    """
    Update the current user username.

    Args:
        session (AsyncSession): The database session.
        body (UpdateUsername): The request body.
        current_user (User): The current user.

    Returns:
        Message: The response message.
    """
    # Check if the new username is the same as the current username
    if current_user.username == body.new_username:
        raise HTTPException(
            status_code=400,
            detail="New username cannot be the same as the current username",
        )

    # Check if the new username meets the required complexity
    username_complexity = is_username_complex(body.new_username)
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
        user_id=current_user.id,
        new_username=body.new_username,
        commit=False,
    )

    # Create update user username event
    update_user_username_event_id = uuid4()
    update_user_username_event_schema = UpdateUserUsernameEvent(
        event_id=update_user_username_event_id,
        user_id=user.id,
        new_username=body.new_username,
    )

    update_user_username_event = await create_outbox_event(
        session=session,
        event_id=update_user_username_event_id,
        event_type="auth_service_update_username",
        data=update_user_username_event_schema.model_dump(mode="json"),
        commit=False,
    )

    update_user_email_username_event_id = uuid4()
    update_user_email_username_event_schema = UpdateUserUsernameEvent(
        event_id=update_user_email_username_event_id,
        user_id=user.id,
        new_username=body.new_username,
    )

    update_user_email_username_event = await create_outbox_event(
        session=session,
        event_id=update_user_email_username_event_id,
        event_type="emails_service_update_username",
        data=update_user_email_username_event_schema.model_dump(mode="json"),
        commit=False,
    )

    await session.commit()
    await session.refresh(user)
    await session.refresh(update_user_username_event)
    await session.refresh(update_user_email_username_event)

    await handle_publish_event(
        session=session,
        event=update_user_username_event,
        event_schema=update_user_username_event_schema,
    )
    await handle_publish_event(
        session=session,
        event=update_user_email_username_event,
        event_schema=update_user_email_username_event_schema,
    )

    return Message(message=f"Username updated to {body.new_username}")


@router.patch(
    "/me/password",
    response_model=Message,
    dependencies=[Depends(GEN_ROLE_CHECKER)],
)
async def update_password(
    session: async_session_dep, body: UpdatePassword, current_user: current_user
) -> Message:
    """
    Update the current user password.

    Args:
        session (AsyncSession): The database session.
        body (UpdatePassword): The request body.
        current_user (User): The current user.

    Returns:
        Message: The response message.
    """
    # Check if the current password is correct
    if not verify_password(body.current_password, current_user.password):
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
        user_id=current_user.id,
        new_password=body.new_password,
        commit=False,
    )

    event_id = uuid4()
    event_schema = UpdateUserPasswordEvent(
        event_id=event_id, user_id=user.id, new_password=user.password
    )

    event = await create_outbox_event(
        session=session,
        event_id=event_id,
        event_type="auth_service_update_password",
        data=event_schema.model_dump(mode="json"),
        commit=False,
    )

    await session.commit()
    await session.refresh(user)

    await handle_publish_event(
        session=session,
        event=event,
        event_schema=event_schema,
    )

    return Message(message="Password updated successfully")
