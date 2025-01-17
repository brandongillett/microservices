from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.models import Users


# CRUD operations for Users
async def get_user(session: AsyncSession, user_id: UUID) -> Users | None:
    """
    Get a user by ID.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.

    Returns:
        Users: The user object or None.
    """
    stmt = select(Users).where(Users.id == user_id)
    result = await session.exec(stmt)
    return result.one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> Users | None:
    """
    Get a user by username.

    Args:
        session (AsyncSession): The database session.
        username (str): The username.

    Returns:
        Users: The user object or None.
    """
    stmt = select(Users).where(Users.username == username)

    result = await session.exec(stmt)
    return result.one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> Users | None:
    """
    Get a user by email.

    Args:
        session (AsyncSession): The database session.
        email (str): The email.

    Returns:
        Users: The user object or None.
    """
    stmt = select(Users).where(Users.email == email)
    result = await session.exec(stmt)
    return result.one_or_none()


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
