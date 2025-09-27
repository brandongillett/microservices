from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.security import get_client_ip


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


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get the read-only database session from the session manager.

    Yields:
        AsyncSession: The database session.
    """
    if session_manager.read_session_maker:
        async with session_manager.read_session_maker() as session:
            yield session
    elif session_manager.session_maker:
        async with session_manager.session_maker() as session:
            yield session
    else:
        raise Exception("Session maker not initialized")


async_session_dep = Annotated[AsyncSession, Depends(get_db)]
async_read_session_dep = Annotated[AsyncSession, Depends(get_read_db)]

client_ip_dep = Annotated[str, Depends(get_client_ip)]
