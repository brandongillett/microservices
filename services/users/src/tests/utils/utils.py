from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.core.security import get_password_hash
from libs.users_lib.models import Users
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)


async def create_random_user_helper(db: AsyncSession) -> Users:
    """
    Create a random user.

    Args:
        db (AsyncSession): The database session.

    Returns:
        Users: The created user.
    """
    username = random_lower_string()
    email = random_email()

    new_user = Users(
        username=username, email=email, password=get_password_hash(test_password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
