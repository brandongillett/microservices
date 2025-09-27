from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException

from libs.auth_lib.api.deps import mgmt_auth_token_dep
from libs.users_lib.api.events import UPDATE_ROLE_ROUTE
from libs.users_lib.crud import (
    get_user_by_email,
    get_user_by_username,
    update_user_role,
)
from libs.users_lib.models import UserRole, Users
from libs.users_lib.schemas import UpdateUserRoleEvent, UserPublic
from libs.utils_lib.api.deps import async_read_session_dep, async_session_dep
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.limiter import Limiter
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.schemas import Message
from src.schemas import UpdateUserRole

router = APIRouter()


@router.get(
    "/users",
    response_model=UserPublic,
    dependencies=[Depends(Limiter("30/minute,300/hour"))],
)
async def get_user_data(
    session: async_read_session_dep,
    user_token: mgmt_auth_token_dep,
    username_email: str,
) -> Users:
    """
    Get the user data.

    Args:
        session (AsyncSession): The database session.
        user_token (TokenData): The user's token data.
        username_email (str): The username or email of the user.

    Returns:
        UserPublic: The user data.
    """
    _ = user_token  # Used for role validation, not needed here

    if "@" in username_email:
        user = await get_user_by_email(session, username_email)
    else:
        user = await get_user_by_username(session, username_email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get(
    "/roles",
    dependencies=[Depends(Limiter("60/minute,1000/hour"))],
)
async def get_roles(user_token: mgmt_auth_token_dep) -> list[str]:
    """
    Get the available roles.

    Args:
        user_token (TokenData): The user's token data.

    Returns:
        list: The available roles.
    """
    _ = user_token  # Used for role validation, not needed here

    roles = [role.value for role in UserRole]
    return roles


@router.patch(
    "/users/{user_id}/role",
    dependencies=[Depends(Limiter("15/minute,100/hour,300/day"))],
    response_model=Message,
)
async def update_role(
    session: async_session_dep,
    user_token: mgmt_auth_token_dep,
    user_id: UUID,
    body: UpdateUserRole,
) -> Message:
    """
    Update the user role.

    Args:
        session (AsyncSession): The database session.
        user_token (TokenData): The user's token data.
        user_id (UUID): The user ID to update.
        body (UpdateUserRole): The request body containing the new role.

    Returns:
        bool: True
    """
    _ = user_token  # Used for role validation, not needed here

    roles = {role.value for role in UserRole}
    if body.new_role not in roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await update_user_role(
        session=session, user_id=user_id, role=UserRole(body.new_role), commit=False
    )

    event_auth_update_role_id = uuid4()
    event_auth_update_role_schema = UpdateUserRoleEvent(
        event_id=event_auth_update_role_id,
        user_id=user.id,
        new_role=UserRole(body.new_role),
    )

    event_auth_update_role = await create_outbox_event(
        session=session,
        event_id=event_auth_update_role_id,
        event_type=UPDATE_ROLE_ROUTE.subject_for("auth"),
        data=event_auth_update_role_schema.model_dump(mode="json"),
        commit=False,
    )

    await session.commit()
    await session.refresh(user)

    await handle_publish_event(
        session=session,
        event=event_auth_update_role,
        event_schema=event_auth_update_role_schema,
    )

    return Message(message=f"{user.username} role updated to {body.new_role}")
