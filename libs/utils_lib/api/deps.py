from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
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


async def get_client_ip(request: Request) -> str:
    """
    Get the client's IP address from the request.

    Args:
        request (Request): The request object

    Returns:
        str: The client's IP address
    """
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        if request.client is not None:
            ip = request.client.host
        else:
            ip = "0.0.0.0"

    return ip


async_session_dep = Annotated[AsyncSession, Depends(get_db)]

client_ip_dep = Annotated[str, Depends(get_client_ip)]
