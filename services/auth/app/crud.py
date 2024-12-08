from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.config import api_settings
from app.core.security import get_password_hash, verify_password
from app.schemas import RefreshTokenCreate, UserCreate
from libs.auth_lib.models import RefreshTokens, Users


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


# CRUD operations for RefreshTokens
async def create_refresh_token(
    session: AsyncSession, refresh_token_create: RefreshTokenCreate
) -> RefreshTokens:
    """
    Create a new refresh token.

    Args:
        session (AsyncSession): The database session.
        refresh_token_create (RefreshTokenCreate): The refresh token create request body.

    Returns:
        RefreshTokens: The created refresh token.
    """
    dbObj = RefreshTokens.model_validate(refresh_token_create)

    session.add(dbObj)
    await session.commit()
    await session.refresh(dbObj)
    return dbObj


async def authenticate_refresh_token(
    session: AsyncSession, user_id: UUID, refresh_jti: UUID
) -> RefreshTokens | None:
    """
    Authenticate a refresh token exists.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        refresh_jti (UUID): The refresh token JTI.

    Returns:
        RefreshTokens: The authenticated refresh token or None.
    """
    session_token = await session.exec(
        select(RefreshTokens).where(
            RefreshTokens.user_id == user_id, RefreshTokens.refresh_jti == refresh_jti
        )
    )
    return session_token.one_or_none()


async def delete_refresh_token(
    session: AsyncSession, user_id: UUID, refresh_token_id: UUID
) -> None:
    """
    Delete a refresh token.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        refresh_token_id (UUID): The refresh token ID.
    """
    session_token = await session.exec(
        select(RefreshTokens).where(
            RefreshTokens.user_id == user_id, RefreshTokens.id == refresh_token_id
        )
    )
    token_to_delete = session_token.one_or_none()

    if token_to_delete:
        await session.delete(token_to_delete)
        await session.commit()


async def get_refresh_token(
    session: AsyncSession, user_id: UUID, refresh_token_id: UUID
) -> RefreshTokens | None:
    """
    Get a refresh token.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
        refresh_token_id (UUID): The refresh token ID.

    Returns:
        RefreshTokens: The refresh token or None.
    """
    result = await session.exec(
        select(RefreshTokens).where(
            RefreshTokens.user_id == user_id, RefreshTokens.id == refresh_token_id
        )
    )
    return result.one_or_none()


async def get_refresh_tokens(
    session: AsyncSession, user_id: UUID
) -> list[RefreshTokens]:
    """
    Get all refresh tokens for a user.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.

    Returns:
        list[RefreshTokens]: The list of refresh tokens.
    """
    result = await session.exec(
        select(RefreshTokens).where(RefreshTokens.user_id == user_id)
    )
    return list(result.all())


async def delete_expired_tokens(session: AsyncSession, user_id: UUID) -> None:
    """
    Delete expired refresh tokens.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
    """
    result = await session.exec(
        select(RefreshTokens).where(
            RefreshTokens.user_id == user_id, RefreshTokens.expires < datetime.utcnow()
        )
    )

    expired_tokens = result.all()

    for token in expired_tokens:
        await session.delete(token)

    await session.commit()


async def delete_max_tokens(session: AsyncSession, user_id: UUID) -> None:
    """
    Delete the oldest refresh tokens if the user has more than the maximum allowed.

    Args:
        session (AsyncSession): The database session.
        user_id (UUID): The user ID.
    """
    await delete_expired_tokens(session, user_id)

    session_tokens = await get_refresh_tokens(session, user_id)

    count = len(session_tokens)

    if count > api_settings.MAX_REFRESH_TOKENS:
        session_tokens.sort(key=lambda token: token.last_used)

        while len(session_tokens) > api_settings.MAX_REFRESH_TOKENS:
            await session.delete(session_tokens[0])
            session_tokens.pop(0)

        await session.commit()
