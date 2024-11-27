from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.v1.deps import async_session_dep, current_user
from app.core.security import (
    is_password_complex,
    is_username_complex,
    verify_password,
)
from app.crud import (
    get_user_by_username,
    update_user_password,
    update_user_username,
)
from app.schemas import (
    Message,
    UpdatePassword,
    UpdateUsername,
    UserPublic,
)

router = APIRouter()


@router.get("/me", response_model=UserPublic)
def my_details(current_user: current_user) -> Any:
    """
    Get the current user details.

    Returns:
        UserPublic: The current user details.
    """
    return current_user


@router.patch("/me/username", response_model=Message)
async def update_user_name(
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
    await update_user_username(
        session=session, user=current_user, new_username=body.new_username
    )

    return Message(message=f"Username updated to {body.new_username}")


@router.patch("/me/password", response_model=Message)
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
    await update_user_password(
        session=session, user=current_user, new_password=body.new_password
    )

    return Message(message="Password updated successfully")
