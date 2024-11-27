from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models import Users
from app.schemas import UserCreate


# CRUD operations for Users
async def create_user(session: AsyncSession, user_create: UserCreate) -> Users:
    """
    Create a new user.

    Args:
        session (AsyncSession): The database session.
        user_create (UserCreate): The user create request body.

    Returns:
        Users: The created user.
    """
    dbObj = Users.model_validate(
        user_create, update={"password": get_password_hash(user_create.password)}
    )
    session.add(dbObj)
    await session.commit()
    await session.refresh(dbObj)

    return dbObj


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


async def authenticate_user(
    session: AsyncSession, username_email: str, password: str
) -> Users | None:
    """
    Authenticate a user.

    Args:
        session (AsyncSession): The database session.
        username_email (str): The username or email.
        password (str): The password.

    Returns:
        Users: The authenticated user or None.
    """
    user = None

    if "@" in username_email:
        user = await get_user_by_email(session, username_email)
    else:
        user = await get_user_by_username(session, username_email)

    if user and verify_password(password, user.password):
        return user

    return None


async def update_user_username(
    session: AsyncSession, user: Users, new_username: str
) -> Users:
    """
    Update the user username.

    Args:
        session (AsyncSession): The database session.
        user (Users): The user object.
        new_username (str): The new username.

    Returns:
        Users: The updated user.
    """
    user.username = new_username
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_password(
    session: AsyncSession, user: Users, new_password: str
) -> Users:
    """
    Update the user password.

    Args:
        session (AsyncSession): The database session.
        user (Users): The user object.
        new_password (str): The new password.

    Returns:
        Users: The updated user.
    """
    user.password = get_password_hash(new_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
