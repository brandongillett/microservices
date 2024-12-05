from sqlmodel.ext.asyncio.session import AsyncSession

from shared_lib.core.security import get_password_hash
from shared_lib.models import Users
from shared_lib.schemas import UserCreate


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