from typing import Any
from uuid import UUID

from faststream.rabbit.fastapi import RabbitRouter

from libs.users_lib.crud import get_user
from libs.utils_lib.api.deps import async_session_dep

rabbit_router = RabbitRouter()


@rabbit_router.subscriber("update_user_username")
async def update_user_username_event(
    session: async_session_dep, data: dict[str, Any]
) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    user = await get_user(session, UUID(data["user_id"]))

    if user:
        user.username = data["new_username"]
        session.add(user)
        await session.commit()
        await session.refresh(user)


@rabbit_router.subscriber("update_user_password")
async def update_user_password_event(
    session: async_session_dep, data: dict[str, Any]
) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    user = await get_user(session, UUID(data["user_id"]))

    if user:
        user.password = data["new_password"]
        session.add(user)
        await session.commit()
        await session.refresh(user)


@rabbit_router.subscriber("update_user_role")
async def update_user_role_event(
    session: async_session_dep, data: dict[str, Any]
) -> None:
    """
    Subscribes to a message to create a user.

    Args:
        user (User): The user to create.
    """
    user = await get_user(session, UUID(data["user_id"]))

    if user:
        user.role = data["role"]
        session.add(user)
        await session.commit()
        await session.refresh(user)
