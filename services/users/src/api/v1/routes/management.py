from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from libs.auth_lib.api.deps import RoleChecker
from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.schemas import Message
from src.crud import update_user_role
from src.events import update_user_role_event
from src.schemas import UpdateUserRole

router = APIRouter()

management_roles = RoleChecker(allowed_roles=["admin", "root"])


@router.get("/roles", dependencies=[Depends(management_roles)])
async def get_roles() -> Any:
    """
    Get the available roles.

    Returns:
        dict: The available roles.
    """
    return auth_lib_security_settings.roles


@router.patch("/role", dependencies=[Depends(management_roles)])
async def update_role(session: async_session_dep, body: UpdateUserRole) -> Message:
    """
    Update the user role.

    Returns:
        bool: True
    """

    if body.role not in auth_lib_security_settings.roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await update_user_role(session=session, user_id=body.user_id, role=body.role)

    await update_user_role_event(user_id=body.user_id, new_role=body.role)

    return Message(message=f"{user.username} role updated to {body.role}")
