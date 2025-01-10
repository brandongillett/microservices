from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from libs.auth_lib.api.deps import RoleChecker
from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.users_lib.crud import get_user_by_email, get_user_by_username
from libs.users_lib.models import Users
from libs.users_lib.schemas import UserPublic
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.schemas import Message
from src.api.events import update_user_role_event
from src.crud import update_user_role
from src.schemas import UpdateUserRole

router = APIRouter()

management_roles = RoleChecker(allowed_roles=["admin", "root"])


@router.get(
    "/users", response_model=UserPublic, dependencies=[Depends(management_roles)]
)
async def get_user_data(
    session: async_session_dep, email: str | None = None, username: str | None = None
) -> Users:
    """
    Get the user data.

    Args:
        session (AsyncSession): The database session.
        email (Optional[str]): The user email.
        username (Optional[str]): The user username.

    Returns:
        UserPublic: The user data.
    """
    if email and username or not email and not username:
        raise HTTPException(status_code=400, detail="Provide either email or username")
    elif email:
        user = await get_user_by_email(session, email)
    elif username:
        user = await get_user_by_username(session, username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/roles", dependencies=[Depends(management_roles)])
async def get_roles() -> Any:
    """
    Get the available roles.

    Returns:
        dict: The available roles.
    """
    return auth_lib_security_settings.roles


@router.patch(
    "/users/{user_id}/role",
    dependencies=[Depends(management_roles)],
    response_model=Message,
)
async def update_role(
    session: async_session_dep, user_id: UUID, body: UpdateUserRole
) -> Message:
    """
    Update the user role.

    Returns:
        bool: True
    """

    if body.new_role not in auth_lib_security_settings.roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    try:
        user = await update_user_role(session=session, user_id=user_id, role=body.new_role, commit=False)

        await update_user_role_event(
            session=session, user_id=user_id, new_role=body.new_role
        )
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    await session.commit()
    await session.refresh(user)

    return Message(message=f"{user.username} role updated to {body.new_role}")
