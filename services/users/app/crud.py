from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.core.security import get_password_hash
from libs.auth_lib.crud import get_user
from libs.auth_lib.models import Users


# CRUD operations for Users
async def update_user_username(
    session: AsyncSession, user_id: UUID, new_username: str
) -> Users:
    """
    Update the user username.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        new_username (str): The new username.

    Returns:
        Users: The updated user.
    """
    user = await get_user(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.username = new_username
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_password(
    session: AsyncSession, user_id: UUID, new_password: str
) -> Users:
    """
    Update the user password.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        new_password (str): The new password.

    Returns:
        Users: The updated user.
    """
    user = await get_user(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.password = get_password_hash(new_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
