from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from libs.auth_lib.api.deps import RoleChecker
from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.schemas import Message
from src.crud import update_user_role

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
async def update_role(session: async_session_dep, user_id: UUID, role: str) -> Message:
    """
    Update the user role.

    Returns:
        bool: True
    """

    if role not in auth_lib_security_settings.roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await update_user_role(session=session, user_id=user_id, role=role)

    await rabbitmq.broker.publish(
        {"user_id": str(user_id), "role": role}, queue="update_user_role"
    )

    return Message(message=f"{user.username} role updated to {role}")
