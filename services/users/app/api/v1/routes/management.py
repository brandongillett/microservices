from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.crud import update_user_role
from libs.auth_lib.api.config import api_settings as auth_lib_api_settings
from libs.auth_lib.api.deps import RoleChecker
from libs.utils_lib.api.deps import async_session_dep

router = APIRouter()

admin_roles = RoleChecker(allowed_roles=["admin"])


@router.get("/roles", dependencies=[Depends(admin_roles)])
async def get_roles() -> Any:
    """
    Get the available roles.

    Returns:
        dict: The available roles.
    """
    return auth_lib_api_settings.roles


@router.get("/update-user-role", dependencies=[Depends(admin_roles)])
async def update_role(session: async_session_dep, user_id: UUID, role: str) -> Any:
    """
    Update the user role.

    Returns:
        bool: True
    """

    if role not in auth_lib_api_settings.roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    await update_user_role(session=session, user_id=user_id, role=role)

    return True
