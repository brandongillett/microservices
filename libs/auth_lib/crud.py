from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.models import Users


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
    result = await session.exec(stmt)  # Execute the statement
    return result.one_or_none()  # Return the single user or None
