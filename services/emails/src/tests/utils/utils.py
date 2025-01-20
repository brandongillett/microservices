from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.core.security import get_password_hash
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)
from src.models import UserEmails


async def create_random_user_helper(db: AsyncSession) -> UserEmails:
    """
    Create a random user.

    Args:
        db (AsyncSession): The database session.

    Returns:
        Users: The created user.
    """
    username = random_lower_string()
    email = random_email()

    new_user = UserEmails(
        username=username, email=email, password=get_password_hash(test_password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
