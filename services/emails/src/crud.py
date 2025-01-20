from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import UserEmails


# CRUD operations for UsersEmails
async def get_user(session: AsyncSession, user_id: UUID) -> UserEmails | None:
    """
    Get a user by ID.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.

    Returns:
        Users: The user object or None.
    """
    stmt = select(UserEmails).where(UserEmails.id == user_id)
    result = await session.exec(stmt)
    return result.one_or_none()


async def get_user_by_username(
    session: AsyncSession, username: str
) -> UserEmails | None:
    """
    Get a user by username.

    Args:
        session (AsyncSession): The database session.
        username (str): The username.

    Returns:
        Users: The user object or None.
    """
    stmt = select(UserEmails).where(UserEmails.username == username)

    result = await session.exec(stmt)
    return result.one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> UserEmails | None:
    """
    Get a user by email.

    Args:
        session (AsyncSession): The database session.
        email (str): The email.

    Returns:
        Users: The user object or None.
    """
    stmt = select(UserEmails).where(UserEmails.email == email)
    result = await session.exec(stmt)
    return result.one_or_none()


async def update_user_username(
    session: AsyncSession, user_id: UUID, new_username: str, commit: bool = True
) -> UserEmails:
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


async def verify_user_email(
    session: AsyncSession, user_id: UUID, commit: bool = True
) -> UserEmails:
    """
    Verify a user.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.

    Returns:
        Users: The verified user.
    """
    user = await get_user(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.verified = True
    session.add(user)

    if commit:
        await session.commit()
        await session.refresh(user)

    return user
