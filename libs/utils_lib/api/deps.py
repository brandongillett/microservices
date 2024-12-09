from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.core.database import session_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get the database session from the session manager.

    Yields:
        AsyncSession: The database session.
    """
    if not session_manager.session_maker:
        raise Exception("Session manager not initialized")
    async with session_manager.session_maker() as session:
        yield session


async_session_dep = Annotated[AsyncSession, Depends(get_db)]
