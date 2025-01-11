from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.core.security import get_password_hash
from libs.users_lib.crud import get_user
from libs.users_lib.models import Users


# CRUD operations for Users
async def update_user_username(
    session: AsyncSession, user_id: UUID, new_username: str, commit: bool = True
) -> Users:
    """
    Update the user username.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        new_username (str): The new username.
        commit (bool): Commit at the end of the operation.

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

    if commit:
        await session.commit()
        await session.refresh(user)

    return user


async def update_user_password(
    session: AsyncSession, user_id: UUID, new_password: str, commit: bool = True
) -> Users:
    """
    Update the user password.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        new_password (str): The new password.
        commit (bool): Commit at the end of the operation.

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

    if commit:
        await session.commit()
        await session.refresh(user)

    return user


async def update_user_role(
    session: AsyncSession, user_id: UUID, role: str, commit: bool = True
) -> Users:
    """
    Update the user role.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        new_role (str): The new role.
        commit (bool): Commit at the end of the operation.

    Returns:
        Users: The updated user.
    """
    user = await get_user(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.role = role
    session.add(user)

    if commit:
        await session.commit()
        await session.refresh(user)

    return user
