from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.crud import get_user
from libs.users_lib.models import Users


async def verify_user_email(
    session: AsyncSession, user_id: UUID, commit: bool = True
) -> Users:
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
